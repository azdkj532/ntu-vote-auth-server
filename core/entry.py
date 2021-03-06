from core.service import BaseEntryRule
from core.models import Entry, OverrideEntry
from django.conf import settings


import logging
logger = logging.getLogger('vote.service')


class NormalEntryRule(BaseEntryRule):
    queryset = Entry.objects.all()
    lookup_field = 'dpt_code'
    lookup_info_kwarg = 'department'
    entry_field = 'kind'


class OverrideEntryRule(BaseEntryRule):
    """
    mapping kind code and student id
    """
    queryset = OverrideEntry.objects.all()
    lookup_field = 'student_id'
    lookup_info_kwarg = 'id'
    entry_field = 'kind'


class UndergraduateEntryRule(BaseEntryRule):
    """
    Rule for undergraduate student, it should return code ends in 'U'.
    It pass the code from @NormalEntryRule which stores in models.Entry actually.
    """
    normal_rule = NormalEntryRule()

    def get_kind(self, student_info):
        if student_info.type_code in settings.UNDERGRADUATE_CODE:
            ret = self.normal_rule.get_kind(student_info)
            return 'NU' if ret is None else ret
        else:
            return None


class GraduateEntryRule(BaseEntryRule):
    """
    Rule for graduate student, it should return code ends in 'G'.
    It pass the code from @NormalEntryRule which stores in models.Entry actually.
    """
    normal_rule = NormalEntryRule()

    def get_kind(self, student_info):
        if student_info.type_code in settings.GRADUATE_CODE:
            ret = self.normal_rule.get_kind(student_info)
            return 'NG' if ret is None else ret
        else:
            return None


class COSSEntryRule(BaseEntryRule):
    """
    Rule for College of Social Science
    """
    target_department = "3\w{3}"

    def get_kind(self, student_info):
        if student_info.type_code in settings.UNDERGRADUATE_CODE:
            if student_info.type_code in settings.GENERAL_CODE:
                return '31'
            else:
                return '3U'
        else:
            if student_info.type_code in settings.GENERAL_CODE:
                return '32'
            else:
                return '3G'


class MedicineEntryRule(BaseEntryRule):
    """
    Rule for College of Medicine
    """
    target_department = "4010"

    def get_kind(self, student_info):
        if student_info.type_code in settings.GENERAL_CODE:
            return "T0"
        else:
            return "4U"
