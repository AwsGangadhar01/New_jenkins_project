import requests
import json
import pandas as pd
import datetime
import logging
import sqlalchemy as sa
from config import username, password, database
from bfdetails import client_id, client_secret
from setup_logger import logger
from pathlib import Path
from sqlalchemy.orm import Session

class BFauth:
    '''
    A class that contains the code used to retrieve the bearer token
    
    Attributes
    ----------
    client_id : 
    ID provided by Brightflag

    client_secret : str
    Secret provided by Brightflag

    '''
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret

    def bf_api_auth(self):
        """Retrieves the bearer token.

        Checks if the status code is 200, if yes, returns the header that will be sent through POST to retrieve the report data 

        """
        url = f"""https://enterprise.brightflag.com/oauth/token?grant_type=client_credentials&client_id={self.client_id}&client_secret={self.client_secret}&"""
        r = requests.post(url, verify=False)
        if r.status_code==200:
            r_json = json.loads(r.text)
            report_headers = {'Authorization': 'Bearer ' + r_json['access_token'],
                            'Content-Type': 'application/json'}
            return report_headers
        else:
            print('Cannot retrieve the access token, status code: ' + r.status_code)

class API_execution:
    '''
    A class that contains a function for retrieving report data
    
    Attributes
    ----------
    report_headers : 
    Generate by calling the bf_api_auth function in the BFauth class

    payload :
    The payload is sent to this class every time it is called, contains the json created in API_Parameters class

    '''
    def __init__(self, payload):
        self.report_headers = BFauth(client_id, client_secret).bf_api_auth()
        self.payload = payload
    def execute(self):
        """
        Retrieves report data. The URL is constant, only the parameters change. Payload is converted into a json string using the json.dumps() function

        The response is  converted to JSON.

        """
        r = requests.post("https://enterprise.brightflag.com/api/v1/reports/", headers=self.report_headers, data=json.dumps(self.payload)).json()
        return r 

class API_parameters:
    '''
    A class used to construct the payloads and manage API calls

    Attributes
    ----------
    currency : 
    Supported currencies: EUR, USD, GBP, AUD, format: ISO code

    reportName :
    Contains the available report name

    StartDateTime:

    Start date/time for the timeframe which the report will run.
    ISO format YYYY-MM-DDThh:mm:ss[.mmm]TZD
    
    endDateTime:
    End date/time for the timeframe which the report will run.
    ISO format YYYY-MM-DDThh:mm:ss[.mmm]TZD

    reportLayout:
    Specifies the structure of the report response. Layouts available: structured, flattened.
    '''
    
    def __init__(self, currency, reportName, startDateTime, endDateTime):
        self.currency = currency
        self.endDateTime = endDateTime
        self.reportLayout = "FLATTENED"
        self.reportName = reportName
        self.startDateTime = startDateTime
    def get_results(self):
        '''
        This function constructs the payload and then call the function that executes the API call.

        If the returned result set contains 5000 results, it indicates that there are additional pages that need to be called in order to retrieve the complete
        data for the given timeframe. All results are put into a pandas dataframe.
            - In this case, I construct a new payload, adding the pagingSessionId and pagingIdentifier variables that can be found in the result set. Then an API call is executed
            and the dateframe appended
        
        When the result set contain less (or more, which is the case with the timekeeper full data dump), it then calls the data cleaning function

        Pandas DF used for convenience, might not be efficient with large datasets due to relatively large memory consumption
        '''
        payload = {
            "currency" : self.currency,
            "endDateTime": self.endDateTime,
            "reportLayout": self.reportLayout,
            "reportName": self.reportName,
            "startDateTime": self.startDateTime
        }
        results = API_execution(payload).execute()
        df_api = pd.DataFrame(results['resultSet'])
        while len(results['resultSet']) == 5000:
            sessionId = results['paging']['sessionId']
            identifier = results['paging']['identifier']
            paging_payload = {
            "currency" : self.currency,
            "endDateTime": self.endDateTime,
            "reportLayout": self.reportLayout,
            "reportName": self.reportName,
            "startDateTime": self.startDateTime,
            "pagingSessionID": sessionId,
            "pagingIdentifier": identifier
            }
            results = API_execution(paging_payload).execute()
            df_api = df_api.append(pd.DataFrame(results['resultSet']))

        data_cleaning(self.reportName, df_api)
    
class data_cleaning:

    '''
    A class that contains functions used for data cleaning

    ...

    Attributes
    ----------
    report_name : 
        the name of the report that's being worked on
    df :
        dataframe that contains the data retrieved through the API

    once these variables are assigned, the select_cleaning function is called which matches the report name to the relevant function. 
    Once this is done, it calls the to_database class, which then moves on to data deduplication and upload

    So the process is

    Iterate through the functions dictionary to find the matching function name -> call the matching function -> run data cleaning -> pass the report to another class
    '''

    def __init__(self, reportName, df_api):
        self.reportName = reportName
        self.df = df_api
        self.select_cleaning_function()
        to_database(self.reportName, self.df)

    def select_cleaning_function(self):
        '''
        Iterates through the function dictionary. Once a matching report name is found in dictionary key, the function that's located in value gets triggered
        '''
        for key, val in self.functions.items():
            if key == self.reportName:
                cleaned_df=val(self)
                break
        return cleaned_df
    
    def test_report_cleaning(self):
        '''
        Cleaning the test report.  

        We start with reading external lookup tables. Both tables are use to add additional details to the report

        Data is joined by using outer joins with the main dataset, self.df
        
        '''
        groups = pd.read_csv(r'role_groups.csv')
        groups = groups[['Role','Group']]

        expense_codes = pd.read_csv(r'expense_codes.csv')
        self.df['Role'] = self.df['Role'].fillna(value="Not Specified")
        self.df = pd.merge(self.df, groups, on=['Role'], how='outer')
        self.df['Expense Code'] = self.df['Expense Code'].str.strip()
        expense_codes['Expense Code'] = expense_codes['Expense Code'].str.strip()
        self.df = pd.merge(self.df, expense_codes, on=['Expense Code'], how='outer')
        self.df = self.df.dropna(subset=['Line ID'])


        return self.df
    def invoice_level_cleaning(self):
        return self.df
    def matter_report_cleaning(self):
        return self.df

    def timekeeper_report_cleaning(self):
        '''
        Cleaning the timekeeper report.  

        The cleaning only involves adding an additional column - group - from the role_group table. Also, it is verified that all Timekeeper rows contain data, as the API
        was putting out empty rows which then break the script later on
        
        '''

        groups = pd.read_csv(r'role_groups.csv')
        groups = groups[['Role','Group']]
        self.df = pd.merge(self.df, groups, on=['Role'], how='outer')
        self.df = self.df[self.df['Timekeeper'].notna()]
        return self.df

    functions = {
    "Reporting API - Invoice Level" : invoice_level_cleaning, 
    "Reporting API - matter report" : matter_report_cleaning,
    "Reporting API - test report" : test_report_cleaning, 
    "Timekeeper Report - full data pull down" : timekeeper_report_cleaning}

class to_database():
    '''
    A class that contains functions for removing duplicate data from databases and uploading data to SQL

    Attributes
    ----------
    tableName : 
    retrieved from the tablename function

    primaryKey :
    contains the primary key column name of the sql table

    df:
    the cleaned dataset 

    engine:
    contains  the sql engine that's returned from sql_engine function

    then there's two functions, one to check for and remove duplicates. The second is for uploading data to sql
    '''
    def __init__(self, reportName, df):
        self.tableName = self.tablename(reportName)
        self.primaryKey = self.pkcolumn()
        self.df = df
        self.engine = self.sql_engine()
        self.check_duplicates()
        self.upload_df()

    def tablename(self, reportName):
        """
        function to match the report name as in brightflag with the table name in sql
        """
        table_names = {
        "Reporting API - Invoice Level" : "invoice_level", 
        "Reporting API - matter report" : "matter_report",
        "Reporting API - test report" : "test_report", 
        "Timekeeper Report - full data pull down" : "timekeeper_report"
        }
        for key, val in table_names.items():
            if key == reportName:
                return val

    def pkcolumn(self):
        """
        finding the primary column id in an sql table that will later be used for removing duplicates
        """
        pkcolumns = {
        "invoice_level" : "Invoice ID", 
        "matter_report" : "Matter Ref",
        "test_report" : "Line ID", 
        "timekeeper_report" : "Timekeeper"
        }
        for key, val in pkcolumns.items():
            if key == self.tableName:
                return val

                
    def sql_engine(self):
        self.engine = sa.create_engine(f"mysql://{username}:{password}@localhost:3306/{database}", echo=True)
        return self.engine

    def check_duplicates(self):
        """
        The idea here is to drop all rows that we currently have in the dataframe because there are multiple columns/datapoints that might have changed. 
        So the solution is just to remove the rows based on the primary key and reupload them again instead of checking multiple parameters

        timekeeper report is different because there's no real primary key that's in the API and we're checking across two columns. However,
        this should essentially result in the whole table getting dropped because we retrieve the whole report anyway through the api
        """
        meta = sa.MetaData()
        table_del = sa.Table(self.tableName, meta, autoload=True, autoload_with=self.engine)
        if self.tableName == "timekeeper_report":
            cond = self.df.apply(lambda row: sa.and_(table_del.c['Timekeeper'] == row['Timekeeper'], table_del.c['Customer MatterID'] == row['Customer MatterID']), axis=1)
        else:
            cond = self.df.apply(lambda row: sa.and_(table_del.c[self.primaryKey] == row[self.primaryKey]), axis=1)
        cond = sa.or_(*cond)
        delete = table_del.delete().where(cond)
        with self.engine.begin() as conn:
                conn.execute(delete)


    def upload_df(self):
        self.df.to_sql(
            self.tableName,
            con=self.engine,
            if_exists = "append",
            index=False
        )

if __name__ == "__main__":
    #getting and formating the start and enddate that is mandatory for an API call
    now = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    enddate = now[:-4]+'Z'
    startdate = datetime.datetime.now()- datetime.timedelta(weeks=12)
    startdate = startdate.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    startdate = startdate[:-4]+'Z'
    for name in ["Reporting API - matter report", "Reporting API - Invoice Level", "Reporting API - test report" ]:
        init_time = API_parameters("USD", name, startdate, enddate)
        init_time.get_results()
    #calling the timekeeper report with hardcoded start date because we want to pull the full report every time we call the api
    init_time = API_parameters("USD", "Timekeeper Report - full data pull down", "2020-11-01T00:00:01.005284Z", enddate) 

    #["Reporting API - matter report", "Reporting API - Invoice Level", "Reporting API - test report" ]