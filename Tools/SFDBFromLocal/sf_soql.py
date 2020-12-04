# -*- coding: utf-8 -*-
#!/usr/bin/python
import json
import os
from simple_salesforce import Salesforce
from salesforce_bulk_api import SalesforceBulkJob
from decouple import config
import logging
from xml.etree import ElementTree

SF_USERNAME = config('CORE_SANDBOX_USER')
SF_PSW = config('CORE_SANDBOX_PASSWORD')
SF_SECURITY = config('CORE_SANDBOX_SECURITY')
SF_DOMAIN = config('CORE_SANDBOX_DOMAIN')
SF_INSTANCE = config('CORE_SANDBOX_URL')

# bulk = SalesforceBulk(username=SF_USERNAME, password=SF_PSW, security_token=SF_SECURITY,domain=SF_DOMAIN)
# job = bulk.create_query_job("Contact", contentType='CSV')
# batch = bulk.query(job, "select Id,LastName from Contact")
# bulk.close_job(job)
# while not bulk.is_batch_done(batch):
#     sleep(10)

# for result in bulk.get_all_results_for_query_batch(batch):
#     reader = csv.DictReader(result, encoding='utf-8')
#     for row in reader:
#         print(row) # dictionary rows

logger = logging.getLogger('salesforce-bulk-api')

class SalesforceAPI:
    PUBLISHING_BATCH_SIZE = 9999
    SUPPORTED_OPERATIONS = {'query','EXPORT_CSV','INSERT', 'UPDATE', 'DELETE', 'UPSERT'}

    def __init__(self,operation,object_name):
        self.salesforce = self.salesforce_session()
        self.session_id = self.salesforce.session_id
        self.async_url = (self.salesforce.base_url
                                    .replace('/data/', '/async/')
                                    .replace('v' + self.salesforce.sf_version,
                                             self.salesforce.sf_version))
        assert operation in self.SUPPORTED_OPERATIONS, '{} is not a valid bulk operation.'.format(operation)
        self.operation = operation    
        supported_objects = {o['name'] for o in self.salesforce.describe()['sobjects']}
        assert object_name in supported_objects, '{} is not a known Salesforce object.'.format(object_name)     
        self.object_name = object_name                        

    def query(self, q):    
        res = self.salesforce.bulk.__getattr__(self.object_name).query(q)
        for d in res:
            print(d)
    
    def export_csv(self,q):
        res = self.salesforce.bulk.__getattr__(self.object_name).query(q)
        with open(self.object_name, mode='w') as f:
            for d in res:
                f.write(json.dumps(d, ensure_ascii=False) + "\n") 
    
    def salesforce_session(self):
        """Returns an authenticated simple_salesforce.Salesforce instance."""
        return Salesforce(
            username=SF_USERNAME,
            password=SF_PSW,
            security_token=SF_SECURITY,
            domain='test',
            version='49.0'
        )

sf = SalesforceAPI('query','OHProperty__c')
sf.query('select Id,Address__c from OHProperty__c')