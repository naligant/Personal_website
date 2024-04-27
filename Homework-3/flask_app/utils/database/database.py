import mysql.connector
import glob
import json
import csv
from io import StringIO
import itertools
import hashlib
import os
import cryptography
from cryptography.fernet import Fernet
from math import pow

class database:

    def __init__(self, purge = False):

        # Grab information from the configuration file
        self.database       = 'db'
        self.host           = '127.0.0.1'
        self.user           = 'master'
        self.port           = 3306
        self.password       = 'master'
        self.tables         = ['institutions', 'positions', 'experiences', 'skills','feedback', 'users']
        
        # NEW IN HW 3-----------------------------------------------------------------
        self.encryption     =  {   'oneway': {'salt' : b'averysaltysailortookalongwalkoffashortbridge',
                                                 'n' : int(pow(2,5)),
                                                 'r' : 9,
                                                 'p' : 1
                                             },
                                'reversible': { 'key' : '7pK_fnSKIjZKuv_Gwc--sZEMKn2zc8VvD6zS96XcNHE='}
                                }
        #-----------------------------------------------------------------------------

    def query(self, query = "SELECT * FROM users", parameters = None):

        cnx = mysql.connector.connect(host     = self.host,
                                      user     = self.user,
                                      password = self.password,
                                      port     = self.port,
                                      database = self.database,
                                      charset  = 'latin1'
                                     )


        if parameters is not None:
            cur = cnx.cursor(dictionary=True)
            cur.execute(query, parameters)
        else:
            cur = cnx.cursor(dictionary=True)
            cur.execute(query)

        # Fetch one result
        row = cur.fetchall()
        cnx.commit()

        if "INSERT" in query:
            cur.execute("SELECT LAST_INSERT_ID()")
            row = cur.fetchall()
            cnx.commit()
        cur.close()
        cnx.close()
        return row

    def createTables(self, purge=False, data_path = 'flask_app/database/'):
        ''' FILL ME IN WITH CODE THAT CREATES YOUR DATABASE TABLES.'''

        #should be in order or creation - this matters if you are using forign keys.
         
        if purge:
            for table in self.tables[::-1]:
                self.query(f"""DROP TABLE IF EXISTS {table}""")
            
        # Execute all SQL queries in the /database/create_tables directory.
        for table in self.tables:
            
            #Create each table using the .sql file in /database/create_tables directory.
            with open(data_path + f"create_tables/{table}.sql") as read_file:
                create_statement = read_file.read()
            self.query(create_statement)

            # Import the initial data
            try:
                params = []
                with open(data_path + f"initial_data/{table}.csv") as read_file:
                    scsv = read_file.read()            
                for row in csv.reader(StringIO(scsv), delimiter=','):
                    params.append(row)
            
                # Insert the data
                cols = params[0]; params = params[1:] 
                self.insertRows(table = table,  columns = cols, parameters = params)
            except:
                print('no initial data')
            
    def insertRows(self, table='table', columns=['x','y'], parameters=[['v11','v12'],['v21','v22']]):
    
        # Check if there are multiple rows present in the parameters
        has_multiple_rows = any(isinstance(el, list) for el in parameters)
        keys, values      = ','.join(columns), ','.join(['%s' for x in columns])
        
        # Construct the query we will execute to insert the row(s)
        query = f"""INSERT IGNORE INTO {table} ({keys}) VALUES """
        if has_multiple_rows:
            for p in parameters:
                query += f"""({values}),"""
            query     = query[:-1] 
            parameters = list(itertools.chain(*parameters))
        else:
            query += f"""({values}) """                      
        
        insert_id = self.query(query,parameters)[0]['LAST_INSERT_ID()']         
        return insert_id
    
    def getResumeData(self):
    
        # queries to gather data from each table
        inst_query = """
            SELECT inst_id, type, name, department, address, city, state, zip
            FROM institutions"""
        pos_query = """
            SELECT position_id, inst_id, title, responsibilities, start_date, end_date
            FROM positions"""
        exp_query = """
            SELECT experience_id, position_id, name, description, hyperlink, start_date, end_date
            FROM experiences"""
        skills_query = """
            SELECT skill_id, experience_id, name, skill_level
            FROM skills"""
        
        #gather data from each table
        inst_data = self.query(inst_query)
        pos_data = self.query(pos_query)
        exp_data = self.query(exp_query)
        skills_data = self.query(skills_query)

        #initialize resume_data
        resume_data = {}

        #gather institutions data and place into resume_data
        for inst in inst_data:
            inst_id = inst['inst_id']
            if inst_id not in resume_data:
                resume_data[inst_id] = {
                    'address': inst['address'],
                    'city': inst['city'],
                    'state': inst['state'],
                    'type': inst['type'],
                    'zip': inst['zip'],
                    'department': inst['department'],
                    'name': inst['name'],
                    'positions': {}
                }

        #gather positions data and place into resume_data
        for pos in pos_data:
            inst_id = pos['inst_id']
            position_id = pos['position_id']
            if inst_id in resume_data:
                resume_data[inst_id]['positions'][position_id] = {
                    'end_date': pos['end_date'],
                    'responsibilities': pos['responsibilities'],
                    'start_date': pos['start_date'],
                    'title': pos['title'],
                    'experiences': {}
                }

        #gather experience_data and place into resume_data
        for exp in exp_data:
            position_id = exp['position_id']
            experience_id = exp['experience_id']
            for inst_id, inst_info in resume_data.items():
                if position_id in inst_info['positions']:
                    inst_info['positions'][position_id]['experiences'][experience_id] = {
                        'description': exp['description'],
                        'end_date': exp['end_date'],
                        'hyperlink': exp['hyperlink'],
                        'name': exp['name'],
                        'skills': {},
                        'start_date': exp['start_date']
                    }
        #gather skills data annd place into resume_data
        for skill in skills_data:
            experience_id = skill['experience_id']
            skill_id = skill['skill_id']
            for inst_id, inst_info in resume_data.items():
                for position_info in inst_info['positions'].values():
                    if experience_id in position_info['experiences']:
                        position_info['experiences'][experience_id]['skills'][skill_id] = {
                            'name': skill['name'],
                            'skill_level': skill['skill_level']
                        }
        return resume_data

#######################################################################################
# AUTHENTICATION RELATED
#######################################################################################
    def createUser(self, email='me@email.com', password='password', role='user'):

        #initial user length
        initial_query = """SELECT * FROM users"""
        initial_users = self.query(initial_query)
        
        #check if email already in database
        emails_query = """ SELECT email FROM users"""
        emails = self.query(emails_query) 
        for x in emails:
            if x['email'] == email:
                return {'success': 0}
        
        #encrypt password
        password = self.onewayEncrypt(password)
        columns = ['role','email', 'password']
        #how to auto increment user_id here?
        parameters = [role, email, password]

        # get keys and values for the row
        keys = ','.join(columns)
        values = ','.join(['%s' for x in columns])
        
        # Construct the query we will execute to insert the row(s)
        query = f"""INSERT IGNORE INTO users ({keys}) VALUES ({values}) """                  
        insert_id = self.query(query,parameters)

        #check if users length increased
        post_query = """SELECT * FROM users"""
        post_users = self.query(initial_query)

        if len(post_users) > len(initial_users):
            return {'success': 1}
        else:
            return {'success': 0}

    def authenticate(self, email='me@email.com', password='password'):
        users_query = """ SELECT * from users"""
        users = self.query(users_query)
        for user in users:
            if (user['email'] == email) and (user['password'] == self.onewayEncrypt(password)):
                return {'success': 1}
        return {'success': 0}

    def onewayEncrypt(self, string):
        encrypted_string = hashlib.scrypt(string.encode('utf-8'),
                                          salt = self.encryption['oneway']['salt'],
                                          n    = self.encryption['oneway']['n'],
                                          r    = self.encryption['oneway']['r'],
                                          p    = self.encryption['oneway']['p']
                                          ).hex()
        return encrypted_string


    def reversibleEncrypt(self, type, message):
        fernet = Fernet(self.encryption['reversible']['key'])
        
        if type == 'encrypt':
            message = fernet.encrypt(message.encode())
        elif type == 'decrypt':
            message = fernet.decrypt(message).decode()

        return message


