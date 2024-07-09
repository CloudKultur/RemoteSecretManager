class Models:
    project = """create table main.projects
(
    id   INTEGER
        primary key,
    name varchar(300)
);"""

    credentials = """create table main.credentials
(
    key        varchar(255),
    value      varchar(640),
    environment varchar(255),
    project_id varchar(50),
    protected  int,
    masked     int,
    raw        int,
    description varchar(255),
    variable_type varchar(255),
    constraint key_project_id
        unique (key, project_id, environment) on conflict rollback
);"""

    options = """create table main.options
(
    key   varchar(50) not null
        primary key,
    value varchar(50) not null
);"""


class Project:
    def __init__(self, id=None, name=None):
        self.id = id
        self.name = name

    def __str__(self):
        return "{: >10} {: <20}".format(str(self.id), self.name)


class Credentials:
    def __init__(self, key=None, value=None, environment=None, project_id=None, protected=False, masked=False, raw=False, description=None, variable_type="env_var"):
        self.key = key
        self.value = value
        self.environment = environment
        self.project_id = project_id
        self.protected = protected
        self.masked = masked
        self.raw = raw
        self.description = description
        self.variable_type = variable_type

    def __str__(self):
        return "{: >20} {: >20} {: >20}".format(self.key, self.value, self.project_id)
    
    def credentials_to_forms(self):
        return {
            "variable_type": self.variable_type,
            "key": self.key,
            "value": self.value,
            "protected": "true" if self.protected else "false",
            "masked": "true" if self.masked else "false",
            "raw": "true" if self.raw else "false",
            "environment_scope": self.environment,
            "description": ""
        }



class Options:
    def __init__(self, key=None, value=None):
        self.key = key
        self.value = value
