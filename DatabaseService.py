import os
import sqlite3
from Converter import project_from_database
from DatabaseModel import Models, Options
from pathlib import Path


class DatabaseService:
    PROJECT_TABLE = "projects"
    CREDENTIALS_TABLE = "credentials"
    OPTIONS_TABLE = "options"

    CURRENT_PROJECT_OPTION = "current_project_id"

    def __init__(self, db):
        models = Models()
        self.db = db
        self.database_name = Path.home() / Path(".rcm/" + db + ".db")
        self.database_name.parents[0].mkdir(parents=True, exist_ok=True)
        exists = os.path.isfile(self.database_name)
        self.connection = sqlite3.connect(str(self.database_name))
        self.connection.row_factory = sqlite3.Row
        if not exists:
            print("[*] Creating the project table...")
            self.connection.execute(models.project)
            print("[*] Creating the credentials table...")
            self.connection.execute(models.credentials)
            print("[*] Creating the options table...")
            self.connection.execute(models.options)
        self.table = self.PROJECT_TABLE

    def create(self, row, table=None):
        if table is None:
            table = self.table
        bindings = "("
        keys = "("
        values = []
        i = 0
        for key, value in row.items():
            bindings += "?"
            keys += key
            values.append(value)
            i += 1
            if i != (len(row)):
                bindings += ", "
                keys += ", "
        bindings += ")"
        keys += ")"
        sql = "INSERT INTO {} {} VALUES {}".format(table, keys, bindings)
        self.connection.execute(sql, values)
        self.connection.commit()

    def read(self, table=None):
        if table is None:
            table = self.table
        sql = "SELECT * FROM {}".format(table)
        cursor = self.connection.execute(sql)
        rows = []
        for row in cursor:
            rows.append(row)
        return rows

    def read_where(self, where, table=None):
        if table is None:
            table = self.table

        selection = self.build_where(where)
        sql = "SELECT * FROM {} {}".format(table, selection)
        cursor = self.connection.execute(sql).fetchall()
        rows = []
        for row in cursor:
            rows.append(row)
        return rows

    def create_or_update(self, row, where, table=None):
        if table is None:
            table = self.table

        selection = self.build_where(where)
        sql = "SELECT EXISTS({0} LIMIT 1)".format(
            "SELECT * FROM {} {}".format(table, selection))
        cursor = self.connection.execute(sql).fetchone()
        if cursor[0] == 1:
            self.update(row, where, table)
        else:
            self.create(row, table)

    def update(self, row, where, table=None):
        if table is None:
            table = self.table
        keys = ""
        values = []
        i = 0
        for key, value in row.items():
            keys += key + " = ?"
            values.append(value)
            i += 1
            if i != len(row):
                keys += ", "
        selection = self.build_where(where)
        sql = "UPDATE {} SET {} {}".format(table, keys, selection)
        self.connection.execute(sql, values)
        self.connection.commit()

    def delete(self, where, table=None):
        if table is None:
            table = self.table
        sql = "DELETE FROM {} WHERE {} = '{}'".format(table, where["key"], where["value"])
        self.connection.execute(sql)
        self.connection.commit()

    def delete_database(self):
        os.remove(self.database_name)

    def delete_table_contents(self, table_name):
        sql = "DELETE FROM {};".format(table_name)
        self.connection.execute(sql)
        self.connection.commit()

    def change_project(self, project_id):
        new_options = Options(self.CURRENT_PROJECT_OPTION, project_id)
        old_options_dict = dict(key=["key"], value=[self.CURRENT_PROJECT_OPTION])
        self.create_or_update(vars(new_options), old_options_dict, self.OPTIONS_TABLE)
        result = self.read_where(dict(key="id", value=project_id), self.PROJECT_TABLE)
        if len(result) >= 1:
            return project_from_database(result[0])
        else:
            return None

    def get_current_project(self):
        try:
            project_option_row = self.read_where(dict(key="key", value=self.CURRENT_PROJECT_OPTION), self.OPTIONS_TABLE)
            if project_option_row:
                project_id = project_option_row[0][1]
                database_project_row = self.read_where(dict(key="id", value=project_id), self.PROJECT_TABLE)
                if database_project_row:
                    return project_from_database(database_project_row[0])
        except Exception as e:
            print(e)
        return None

    def build_where(self, where):
        if len(where["key"]) > 1 and isinstance(where["key"], list):
            selection = "WHERE " + " and ".join(
                ["{} = '{}'".format(where["key"][i], where["value"][i]) for i in range(len(where["key"]))]
            )
        elif isinstance(where["key"], list):
            selection = "WHERE {} = '{}'".format(where["key"][0], where["value"][0])
        else:
            selection = "WHERE {} = '{}'".format(where["key"], where["value"])
        return selection

