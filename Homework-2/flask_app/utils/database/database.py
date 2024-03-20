import mysql.connector
import glob
import json
import csv
from io import StringIO
import itertools
import datetime
class database:

    def __init__(self, purge = False):

        # Grab information from the configuration file
        self.database       = 'db'
        self.host           = '127.0.0.1'
        self.user           = 'master'
        self.port           = 3306
        self.password       = 'master'

    def query(self, query = "SELECT CURDATE()", parameters = None):

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

    def about(self, nested=False):    
        query = """select concat(col.table_schema, '.', col.table_name) as 'table',
                          col.column_name                               as column_name,
                          col.column_key                                as is_key,
                          col.column_comment                            as column_comment,
                          kcu.referenced_column_name                    as fk_column_name,
                          kcu.referenced_table_name                     as fk_table_name
                    from information_schema.columns col
                    join information_schema.tables tab on col.table_schema = tab.table_schema and col.table_name = tab.table_name
                    left join information_schema.key_column_usage kcu on col.table_schema = kcu.table_schema
                                                                     and col.table_name = kcu.table_name
                                                                     and col.column_name = kcu.column_name
                                                                     and kcu.referenced_table_schema is not null
                    where col.table_schema not in('information_schema','sys', 'mysql', 'performance_schema')
                                              and tab.table_type = 'BASE TABLE'
                    order by col.table_schema, col.table_name, col.ordinal_position;"""
        results = self.query(query)
        if nested == False:
            return results

        table_info = {}
        for row in results:
            table_info[row['table']] = {} if table_info.get(row['table']) is None else table_info[row['table']]
            table_info[row['table']][row['column_name']] = {} if table_info.get(row['table']).get(row['column_name']) is None else table_info[row['table']][row['column_name']]
            table_info[row['table']][row['column_name']]['column_comment']     = row['column_comment']
            table_info[row['table']][row['column_name']]['fk_column_name']     = row['fk_column_name']
            table_info[row['table']][row['column_name']]['fk_table_name']      = row['fk_table_name']
            table_info[row['table']][row['column_name']]['is_key']             = row['is_key']
            table_info[row['table']][row['column_name']]['table']              = row['table']
        return table_info



    def createTables(self, purge=False, data_path = 'flask_app/database/'):

        #destroy tables in the beginning to avoid duplicate data
        if purge:
            self.query("DROP TABLE IF EXISTS feedback")
            self.query("DROP TABLE IF EXISTS skills")
            self.query("DROP TABLE IF EXISTS experiences")
            self.query("DROP TABLE IF EXISTS positions")
            self.query("DROP TABLE IF EXISTS institutions")
        files = ['institutions', 'positions', 'experiences', 'skills', 'feedback']

        #read sql files and create tables
        for file in files:
            table_path = data_path + 'create_tables/' + file + '.sql'
            with open(table_path, 'r') as reader:
                sql_file = reader.read()
            sql_commands = sql_file.split(';')
            for command in sql_commands:
                if command.strip() and not command.strip().lower().startswith('select'):
                    self.query(command)

            #read parameters from csv file
            if file != 'feedback':
                parameters = []
                csv_path = data_path + 'initial_data/' + file + '.csv'
                with open(csv_path, 'r') as csv_reader:
                    rows = csv.DictReader(csv_reader)
                    for row in rows:
                        parameters.append([row[column] for column in rows.fieldnames])


            #insert rows in created tables
            if file == 'institutions':
                self.insertRows(table='institutions', columns=['inst_id', 'type', 'name', 'department', 'address', 'city', 'state', 'zip'], parameters=parameters)
            elif file == 'positions':
                self.insertRows(table='positions', columns=['position_id', 'inst_id', 'title', 'responsibilities', 'start_date', 'end_date'], parameters=parameters)
            elif file == 'experiences':
                self.insertRows(table='experiences', columns=['experience_id', 'position_id', 'name', 'description', 'hyperlink', 'start_date', 'end_date'], parameters=parameters)
            elif file == 'skills':
                self.insertRows(table='skills', columns=['skill_id', 'experience_id', 'name', 'skill_level'], parameters=parameters)

        print('I create and populate database tables.')

    def insertRows(self, table='table', columns=['x','y'], parameters=[['v11','v12'],['v21','v22']]):

        #query to insert row into table and columns given
        sql_insert = "INSERT INTO {} ({}) VALUES ({})".format(table, ','.join(columns) ,','.join(['%s'] * len(columns)))

        #make parameters into tuples for each object
        flat_parameters = [tuple(row) for row in parameters]

        #go through each object and add it into the table
        for i in flat_parameters:
            i = tuple(None if param == 'NULL' else param for param in i)
            self.query(query=sql_insert, parameters=i)
        print('I insert rows to tables')
        


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
