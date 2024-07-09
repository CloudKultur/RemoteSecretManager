from DatabaseModel import Project, Options, Credentials


def project_from_database(dictionary):
    return Project(id=dictionary["id"], name=dictionary["name"])


def options_from_database(dictionary):
    return Options(key=dictionary["key"], value=dictionary["value"])


def credentials_from_database(dictionary):
    return Credentials(key=dictionary["key"], value=dictionary["value"], environment=dictionary["environment"], project_id=dictionary["project_id"], protected=dictionary["protected"]==1, masked=dictionary["masked"]==1, raw=dictionary["raw"]==1, description=dictionary["description"], variable_type=dictionary["variable_type"])
