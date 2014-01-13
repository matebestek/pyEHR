from abc import ABCMeta, abstractmethod
from openehr.utils import decode_dict
import time


class RecordsFactory(object):
    """
    This class acts as a factory to create :class:`PatientRecord` and
    :class:`ClinicalRecord` objects from documents
    """

    @staticmethod
    def create_patient_record(document):
        """
        Create a :class:`PatientRecord` object from the given document

        :param document: the document that must be wrapped
        :type document: dictionary
        :return: a :class:`PatientRecord` object

        >>> from bson import ObjectId
        >>> doc = {
        ...   u'creation_time': 1385569688.39202, 'last_update': 1385570688.39202,
        ...   u'active': True, u'ehr_records': []
        ... }
        >>> record = RecordsFactory.create_patient_record(doc)
        >>> print('%f %f %r %r' % (record.creation_time, record.last_update,
        ...       record.active, record.ehr_records))
        1385569688.392020 1385570688.392020 True []
        >>> print repr(record.record_id)
        None
        >>> doc['_id'] = ObjectId('000000000000000000000001')
        >>> record = RecordsFactory.create_patient_record(doc)
        >>> print repr(record.record_id)
        ObjectId('000000000000000000000001')
        """
        document = decode_dict(document)
        return PatientRecord(document['ehr_records'],
                             document['creation_time'],
                             document['last_update'],
                             document['active'],
                             document.get('_id'))

    @staticmethod
    def create_clinical_record(document, unload_object=False):
        """
        Create a :class:`ClinicalRecord` object from the given document

        :param document: the document that must be wrapped
        :type document: dictionary
        :param unload_object: if True only the record_id field of the :class:`ClinicalRecord` object
          will have a value, if True the document will be completely mapped
        :type unload_object: boolean
        :return: a :class:`ClinicalRecord` object

        >>> from bson import ObjectId
        >>> doc = {
        ...   u'creation_time': 1385569688.39202, u'last_update': 1385570688.39202,
        ...   u'active': True, u'ehr_data': {'field1': 'value1', 'field2': 'value2'}
        ... }
        >>> record = RecordsFactory.create_clinical_record(doc)
        >>> print ('%f %f %r %r' % (record.creation_time, record.last_update,
        ...        record.active, record.ehr_data))
        1385569688.392020 1385570688.392020 True {'field2': 'value2', 'field1': 'value1'}
        >>> print repr(record.record_id)
        None
        >>> doc['_id'] = ObjectId('000000000000000000000001')
        >>> record = RecordsFactory.create_clinical_record(doc)
        >>> print repr(record.record_id)
        ObjectId('000000000000000000000001')
        >>> record.ehr_data is None
        False
        >>> record = RecordsFactory.create_clinical_record(doc, unload_object=True)
        >>> print repr(record.record_id)
        ObjectId('000000000000000000000001')
        >>> record.ehr_data is None
        True
        """
        document = decode_dict(document)
        if not unload_object:
            return ClinicalRecord(document['ehr_data'],
                                  document['creation_time'],
                                  document['last_update'],
                                  document['active'],
                                  document.get('_id'))
        else:
            return ClinicalRecord(ehr_data=None,
                                  record_id=document.get('_id'))


class Record(object):
    """
    Generic record abstract class containing record's base fields.

    :ivar record_id: record's unique identifier
    :ivar creation_time: timestamp of record's creation
    :ivar last_update: timestamp of the last update occurred on the record
    :ivar active: boolean representing if the record is active or not
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def __init__(self, creation_time, last_update=None, active=True, record_id=None):
        self.creation_time = creation_time
        self.last_update = last_update or creation_time
        self.active = active
        self.record_id = record_id

    @abstractmethod
    def _to_document(self):
        doc = {
            'creation_time': self.creation_time,
            'last_update': self.last_update,
            'active': self.active
        }
        if self.record_id:
            doc['_id'] = self.record_id
        return doc


class PatientRecord(Record):
    """
    Class representing a patient's record

    :ivar ehr_records: the list of clinical records related to this patient
    """

    def __init__(self, ehr_records=None, creation_time=None,
                 last_update=None, active=True, record_id=None):
        super(PatientRecord, self).__init__(creation_time or time.time(),
                                            last_update, active, record_id)
        self.ehr_records = ehr_records or []

    def _to_document(self):
        """
        >>> rec = PatientRecord([], 1385569688.39202, 1385570688.39202)
        >>> print rec._to_document()
        {'active': True, 'ehr_records': [], 'creation_time': 1385569688.39202, 'last_update': 1385570688.39202}
        """
        doc = super(PatientRecord, self)._to_document()
        doc['ehr_records'] = [ehr.record_id for ehr in self.ehr_records]
        return doc


class ClinicalRecord(Record):
    """
    Class representing a clinical record

    :ivar ehr_data: clinical data in OpenEHR syntax
    """

    def __init__(self, ehr_data, creation_time=None, last_update=None,
                 active=True, record_id=None):
        super(ClinicalRecord, self).__init__(creation_time or time.time(),
                                             last_update, active, record_id)
        self.ehr_data = ehr_data

    def _to_document(self):
        """
        >>> rec = ClinicalRecord({'field1': 'value1', 'field2': 'value2'}, 1385569688.39202)
        >>> print rec._to_document()
        {'active': True, 'ehr_data': {'field2': 'value2', 'field1': 'value1'}, 'creation_time': 1385569688.39202, 'last_update': 1385569688.39202}
        """
        doc = super(ClinicalRecord, self)._to_document()
        doc['ehr_data'] = self.ehr_data
        return doc
