import re
from core import service
from core.models import Record, AuthCode
from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from urllib.error import URLError
from .utils import event_available, logger, error

@api_view(['POST'])
def api(request):
    # Check event timespan
    if not event_available():
        return error('service_closed')

    # Check parameters
    try:
        api_key = request.DATA['api_key']
        version = request.DATA['version']
        internal_id = request.DATA['cid']
        raw_student_id = request.DATA['uid']
        station_id = request.DATA['station']

    except KeyError:
        logger.exception('Invalid parameters')
        return error('params_invalid')

    else:
        # Assert API key and version match
        if api_key != settings.API_KEY:
            return error('unauthorized', status.HTTP_401_UNAUTHORIZED)
        elif version != '1':
            return error('version_not_supported')

        # Parse student ID
        if re.match(r'[A-Z]\d{2}[0-9A-Z]\d{6}', raw_student_id) and re.match(r'[0-9a-f]{8}', internal_id):
            student_id = raw_student_id[:-1]
            revision = int(raw_student_id[-1:])
            logger.info('Station %s request for card %s[%s]', station_id, student_id, revision)
        else:
            logger.info('Station %s request for card %s (%s)', station_id, raw_student_id, internal_id)
            return error('card_invalid')

    # Call ACA API
    try:
        aca_info = service.to_student_id(internal_id)

    except URLError:
        logger.exception('Failed to connect to ACA server')
        return error('external_error', status.HTTP_502_BAD_GATEWAY)

    except service.ExternalError as e:
        logger.exception('Card rejected by ACA server, reason %s', e.reason)
        if e.reason == 'card_invalid' or e.reason == 'student_not_found':
            return error('card_invalid')
        elif e.reason == 'card_blacklisted':
            return error('card_suspicious')
        return error('external_error', status.HTTP_502_BAD_GATEWAY)

    else:
        if aca_info.id != student_id:
            logger.info('ID %s returned instead', aca_info.id)
            return error('card_suspicious')

    # Check vote record
    try:
        record = Record.objects.get(student_id=student_id)
        if record.revision != revision:
            # ACA claim the card valid!
            logger.info('Expect revision %s, recorded %s', revision, record.revision)
            return error('card_suspicious')

        if record.state != Record.AVAILABLE:
            return error('duplicate_entry')

    except Record.DoesNotExist:
        pass

    # Check if cooperative member
    is_coop = service.is_coop_member(student_id)

    # Build up kind identifier
    try:
        college = settings.COLLEGE_IDS[aca_info.college]
    except KeyError:
        # Use student ID as an alternative
        logger.warning('No matching college for ACA entry %s', aca_info.college)
        college = student_id[3]

        # In rare cases, we may encounter students without colleges
        if college not in settings.COLLEGE_NAMES:
            logger.warning('No matching college for ID %s', college)
            college = '0'

    kind = college + ('1' if is_coop else '0')

    # Filter out unqualified students
    # i.e. non-cooperative members who belong to no college
    if kind not in settings.KINDS:
        return error('unqualified')
    else:
        kind_name = settings.KINDS[kind]

    code = AuthCode.objects.filter(kind=kind, issued=False).first()
    if code:
        entry = Record()
        entry.student_id = student_id
        entry.revision = revision
        entry.state = Record.USED
        entry.save()

        code.issued = True
        code.save()
    else:
        logger.info('Auth codes of kind %s have used up', kind)
        return error('out_of_auth_code', status=status.HTTP_503_SERVICE_UNAVAILABLE)

    logger.info('Auth code issued: %s', kind)
    return Response({'status': 'success', 'uid': student_id, 'type': kind_name, 'code': code.code})
