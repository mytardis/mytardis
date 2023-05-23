"""
 Command for stress-testing mytardis by inserting large numbers of dummy objects
 into the database.
"""

# pylint: disable=R1702,W0311

import sys

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User, Group

# from numpy.random import default_rng

from ...auth.localdb_auth import django_user, django_group
from ...models.access_control import (
    ExperimentACL,
    DatasetACL,
    DatafileACL,
)  # ProjectACL,
from ...models import (
    Experiment,
    Dataset,
    DataFile,
    Schema,  # Project,
    ParameterName,
    DatafileParameterSet,
    DatafileParameter,
    DatasetParameterSet,
    DatasetParameter,
    ExperimentParameterSet,
    ExperimentParameter,
)  # , ProjectParameterSet, ProjectParameter)
from ...models.facility import Facility
from ...models.instrument import Instrument

# from ...models.institution import Institution

hundred_words = [
    "absurd",
    "act",
    "addicted",
    "advert",
    "angry",
    "apathetic",
    "apparel",
    "arrogant",
    "barbarous",
    "best",
    "bite",
    "bless",
    "blink",
    "blow",
    "boundless",
    "calculate",
    "calculator",
    "cannon",
    "care",
    "check",
    "coil",
    "compare",
    "cool",
    "dislike",
    "doubt",
    "drag",
    "encourage",
    "extra",
    "feeble",
    "fool",
    "function",
    "glue",
    "hall",
    "hellish",
    "history",
    "humdrum",
    "impartial",
    "jar",
    "lame",
    "leather",
    "literate",
    "little",
    "lively",
    "messy",
    "mine",
    "mother",
    "muddled",
    "mundane",
    "naughty",
    "neat",
    "needless",
    "nest",
    "nose",
    "nostalgic",
    "oblong",
    "perfect",
    "perpetual",
    "pest",
    "planes",
    "race",
    "remarkable",
    "replace",
    "roomy",
    "rule",
    "run",
    "safe",
    "sail",
    "secretive",
    "shoes",
    "splendid",
    "staking",
    "steep",
    "steer",
    "stiff",
    "street",
    "suggest",
    "talented",
    "talk",
    "tangy",
    "thank",
    "thick",
    "thought",
    "tie",
    "toes",
    "tough",
    "treatment",
    "ubiquitous",
    "ultra",
    "uncle",
    "unhealthy",
    "unruly",
    "unwritten",
    "useless",
    "vase",
    "watch",
    "whirl",
    "windy",
    "woman",
    "wrench",
    "yawn",
]


def create_acl(
    entity,
    entity_type,
    object,
    download=False,
    write=False,
    sensitive=False,
    delete=False,
    isowner=False,
):

    if entity_type == "django_user":
        """if object.get_ct().model == "project":
        testacl = ProjectACL(project=object,
                            user=entity,
                            canRead=True,
                            canDownload = download,
                            canWrite=write,
                            canSensitive=sensitive,
                            canDelete=delete,
                            isOwner=isowner,
                            aclOwnershipType=ProjectACL.OWNER_OWNED)
        testacl.save()"""
        if object.get_ct().model == "experiment":
            testacl = ExperimentACL(
                experiment=object,
                user=entity,
                canRead=True,
                canDownload=download,
                canWrite=write,
                canSensitive=sensitive,
                canDelete=delete,
                isOwner=isowner,
                aclOwnershipType=ExperimentACL.OWNER_OWNED,
            )
            testacl.save()
        if object.get_ct().model == "dataset":
            testacl = DatasetACL(
                dataset=object,
                user=entity,
                canRead=True,
                canDownload=download,
                canWrite=write,
                canSensitive=sensitive,
                canDelete=delete,
                isOwner=isowner,
                aclOwnershipType=DatasetACL.OWNER_OWNED,
            )
            testacl.save()
        if object.get_ct().model.replace(" ", "") == "datafile":
            testacl = DatafileACL(
                datafile=object,
                user=entity,
                canRead=True,
                canDownload=download,
                canWrite=write,
                canSensitive=sensitive,
                canDelete=delete,
                isOwner=isowner,
                aclOwnershipType=DatafileACL.OWNER_OWNED,
            )
            testacl.save()

    if entity_type == "django_group":
        """if object.get_ct().model == "project":
        testacl = ProjectACL(project=object,
                            group=entity,
                            canRead=True,
                            canDownload = download,
                            canWrite=write,
                            canSensitive=sensitive,
                            canDelete=delete,
                            isOwner=isowner,
                            aclOwnershipType=ProjectACL.OWNER_OWNED)
        testacl.save()"""
        if object.get_ct().model == "experiment":
            testacl = ExperimentACL(
                experiment=object,
                group=entity,
                canRead=True,
                canDownload=download,
                canWrite=write,
                canSensitive=sensitive,
                canDelete=delete,
                isOwner=isowner,
                aclOwnershipType=ExperimentACL.OWNER_OWNED,
            )
            testacl.save()
        if object.get_ct().model == "dataset":
            testacl = DatasetACL(
                dataset=object,
                group=entity,
                canRead=True,
                canDownload=download,
                canWrite=write,
                canSensitive=sensitive,
                canDelete=delete,
                isOwner=isowner,
                aclOwnershipType=DatasetACL.OWNER_OWNED,
            )
            testacl.save()
        if object.get_ct().model.replace(" ", "") == "datafile":
            testacl = DatafileACL(
                datafile=object,
                group=entity,
                canRead=True,
                canDownload=download,
                canWrite=write,
                canSensitive=sensitive,
                canDelete=delete,
                isOwner=isowner,
                aclOwnershipType=DatafileACL.OWNER_OWNED,
            )
            testacl.save()


def create_owner_acl(owner, object):
    create_acl(
        owner,
        django_user,
        object,
        download=True,
        write=True,
        sensitive=True,
        delete=True,
        isowner=True,
    )


def create_user_acl(user, object):
    create_acl(user, django_user, object)


def create_group_acl(group, object, group_flag):
    if group_flag == "adm":
        create_acl(
            group, django_group, object, download=True, write=True, sensitive=True
        )
    elif group_flag == "rd":
        create_acl(group, django_group, object, download=True)
    else:
        create_acl(group, django_group, object)


class Command(BaseCommand):

    help = "Stress-test the database by inserting/removing objects"

    def add_arguments(self, parser):
        """
        Will create N Projects, N*100 Experiments, N*10000 Datasets, and
        N*1000000 DataFiles.
        E.g. N=1 we will create 1M Datafiles, 10000 Datasets,
        100 Experiments, and 1 Project.
        """
        parser.add_argument(
            "--N",
            help="number of datafile objects to create. Choose 1 or 100",
            type=int,
        )

        parser.add_argument(
            "--user",
            help="User to whom the objects belong (for testing ease).",
            type=str,
        )

        parser.add_argument(
            "--dummypass", help="Dummy password for created test users.", type=str
        )

    def handle(self, *args, **options):
        username = options.get("user", None)
        dummypass = options.get("dummypass", None)

        if not username:
            raise CommandError("Please specify a username using --user USERNAME")
        if not dummypass:
            raise CommandError(
                "Please specify a dummy password using --dummypass DUMMYPASS"
            )
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError('Username: "' + str(username) + '" not found.')

        # n_proj = options.get('N', 1)
        # if n_proj != 100:
        #    sys.stderr.write("Defaulting to N=1, 1 Project -> 1M datafiles.\n")
        #    n_proj = 1

        n_exp = options.get("N", 1)
        if n_exp != 100:
            sys.stderr.write("Defaulting to N=1, 1 Experiment -> 10,000 datafiles.\n")
            n_exp = 1

        # Create 20 dummy users using input_user credentials. Create 15 groups
        # and populate with relevant users
        sys.stderr.write("Creating groups and users...\n")
        test_users = {}
        test_groups = {}
        for x in [1, 25, 50, 75, 100]:
            test_users[str(x)] = {}
            test_groups[str(x)] = {}
            for y in ["adm", "rd", "r"]:
                test_username = user.username + "_test_" + y + "_" + str(x)
                test_users[str(x)][y] = User.objects.create_user(
                    username=test_username, password=dummypass
                )
                test_users[str(x)][y].save()
                test_group_name = "STRESSTEST_" + y + "_" + str(x)
                test_groups[str(x)][y] = Group.objects.create(name=test_group_name)
                test_groups[str(x)][y].save()
                test_users[str(x)][y].groups.add(test_groups[str(x)][y])
                test_users[str(x)][y].save()
            test_username = user.username + "_test_nogrp_" + str(x)
            test_users[str(x)]["nogrp"] = User.objects.create_user(
                username=test_username, password=dummypass
            )
            test_users[str(x)]["nogrp"].save()
        sys.stderr.write("Done.\n")

        sys.stderr.write("Creating Schemas and parameterNames...\n")
        # Create 4 dummy schemas for use with all the models
        # test_schema_proj = Schema.objects.create(
        #    namespace="http://stress.test/project",
        #    type=Schema.PROJECT)
        # test_schema_proj.save()
        test_schema_exp = Schema.objects.create(
            namespace="http://stress.test/experiment", type=Schema.EXPERIMENT
        )
        test_schema_exp.save()
        test_schema_set = Schema.objects.create(
            namespace="http://stress.test/dataset", type=Schema.DATASET
        )
        test_schema_set.save()
        test_schema_file = Schema.objects.create(
            namespace="http://stress.test/datafile", type=Schema.DATAFILE
        )
        test_schema_file.save()

        test_parnames = {}
        # Create 5 parameter names fo each schema, 1 of which should be sensitive
        for schema in [
            test_schema_exp,
            test_schema_set,
            test_schema_file,
        ]:  # test_schema_proj,
            type = schema.namespace.split("/")[-1]
            test_parnames[type] = {}
            for x in ["Param_1", "Param_2", "Param_3", "Param_4", "Param_sens"]:
                sens_flag = False
                if x == "Param_sens":
                    sens_flag = True
                test_parnames[type][x] = ParameterName.objects.create(
                    schema=schema,
                    name=x,
                    data_type=ParameterName.STRING,
                    sensitive=sens_flag,
                )
                test_parnames[type][x].save()
        sys.stderr.write("Done.\n")

        sys.stderr.write(
            "Creating managing group, institution, facility, and instrument...\n"
        )
        # Create managing group, Institution, Facility, and instrument for test objects
        test_manage_group = Group(name="STRESSTEST_Group")
        test_manage_group.save()
        test_manage_group.user_set.add(user)
        # test_institution = Institution(name="STRESSTEST_Institute",
        #                               manager_group=test_manage_group)
        # test_institution.save()
        test_facility = Facility(
            name="STRESSTEST_Facility", manager_group=test_manage_group
        )  # ,institution=test_institution)
        test_facility.save()
        test_instrument = Instrument(
            name="STRESSTEST_Instrument", facility=test_facility
        )
        test_instrument.save()
        sys.stderr.write("Done.\n")

        # define the default rng to be used throughout the object creations
        # rng = default_rng()

        # if n_proj == 100:
        # Generate random samples for level below
        """rng_proj_dict = {"1" : [0],#rng.choice(100, size=1, replace=False),
                        "25" : list(range(0, 25)),#rng.choice(100, size=25, replace=False),
                        "50" : list(range(0, 50)),#rng.choice(100, size=50, replace=False),
                        "75" : list(range(0, 75))}#rng.choice(100, size=75, replace=False)}

        sys.stderr.write("Creating Projects...\n")
        #Create the projects
        for idx_proj in range(n_proj):
            # Create project
            test_raid = "STRESSTEST_"+hundred_words[idx_proj]
            testproject = Project(name=test_raid, raid=test_raid)
            testproject.created_by = user
            testproject.principal_investigator = user
            testproject.institutions.add(test_institution)
            testproject.save()
            #Create ACL for "owner"
            create_owner_acl(user, testproject)
            #Create parameterset and parameters for project
            parset = ProjectParameterSet(schema=test_schema_proj,
                                         project=testproject)
            parset.save()
            for paramname in test_parnames["project"].values():
                sens_param = False
                if paramname.name == "Param_sens":
                    sens_param = True
                df_parameter = ProjectParameter(name=paramname,
                                                parameterset=parset,
                                                string_value=paramname.name,
                                                sensitive_metadata=sens_param)
                df_parameter.save()

            # create ACLs for groups/users with 100% access
            for y in ["adm","rd","r"]:
                create_group_acl(test_groups["100"][y], testproject, y)
            create_user_acl(test_users["100"]["nogrp"], testproject)

            if n_proj == 100:
                # if idx in random sample list, add acl for appropriate group/users
                for key, val in rng_proj_dict.items():
                    if idx_exp in val:
                        for y in ["adm","rd","r"]:
                            create_group_acl(test_groups[key][y], testproject, y)
                        create_user_acl(test_users[key]["nogrp"], testproject)
            else:
                for key, val in rng_proj_dict.items():
                    for y in ["adm","rd","r"]:
                        create_group_acl(test_groups[key][y], testproject, y)
                    create_user_acl(test_users[key]["nogrp"], testproject)

            # Generate random samples for level below"""
        rng_exp_dict = {
            "1": [0],  # rng.choice(100, size=1, replace=False),
            "25": list(range(0, 25)),  # rng.choice(100, size=25, replace=False),
            "50": list(range(0, 50)),  # rng.choice(100, size=50, replace=False),
            "75": list(range(0, 75)),
        }  # rng.choice(100, size=75, replace=False)}

        # sys.stderr.write("Project "+str(idx_proj+1)+" created...\n")
        sys.stderr.write("Creating Experiments...\n")

        # Create the experiments
        for idx_exp in range(n_exp):  # range(100):
            test_title = "STRESSTEST_" + hundred_words[idx_exp]
            testexp = Experiment(title=test_title)  # , project=testproject)
            testexp.created_by = user
            testexp.save()
            # Create ACL for "owner"
            create_owner_acl(user, testexp)
            # Create parameterset and parameters for experiment
            parset = ExperimentParameterSet(schema=test_schema_exp, experiment=testexp)
            parset.save()
            for paramname in test_parnames["experiment"].values():
                df_parameter = ExperimentParameter(
                    name=paramname, parameterset=parset, string_value=paramname.name
                )
                df_parameter.save()

            # create ACLs for groups/users with 100% access
            for y in ["adm", "rd", "r"]:
                create_group_acl(test_groups["100"][y], testexp, y)
            create_user_acl(test_users["100"]["nogrp"], testexp)
            # if idx in random sample list, add acl for appropriate group/users
            for key, val in rng_exp_dict.items():
                if idx_exp in val:
                    for y in ["adm", "rd", "r"]:
                        create_group_acl(test_groups[key][y], testexp, y)
                    create_user_acl(test_users[key]["nogrp"], testexp)

            # Generate random samples for level below
            rng_set_dict = {
                "1": [80],  # rng.choice(100, size=1, replace=False),
                "25": list(range(0, 25)),  # rng.choice(100, size=25, replace=False),
                "50": list(range(0, 50)),  # rng.choice(100, size=50, replace=False),
                "75": list(range(0, 75)),
            }  # rng.choice(100, size=75, replace=False)}

            sys.stderr.write("Experiment " + str(idx_exp + 1) + " created...\n")
            sys.stderr.write("Creating Datasets...\n")

            # Create the datasets
            for idx_set in range(100):
                test_desc = "STRESSTEST_" + hundred_words[idx_set]
                testset = Dataset(description=test_desc)
                testset.save()
                testset.experiments.add(testexp)
                testset.instrument = test_instrument
                testset.save()
                # Create ACL for "owner"
                create_owner_acl(user, testset)
                # Create parameterset and parameters for dataset
                parset = DatasetParameterSet(schema=test_schema_set, dataset=testset)
                parset.save()
                for paramname in test_parnames["dataset"].values():
                    df_parameter = DatasetParameter(
                        name=paramname, parameterset=parset, string_value=paramname.name
                    )
                    df_parameter.save()

                # create ACLs for groups/users with 100% access
                for y in ["adm", "rd", "r"]:
                    create_group_acl(test_groups["100"][y], testset, y)
                create_user_acl(test_users["100"]["nogrp"], testset)
                # if idx in random sample list, add acl for appropriate group/users
                for key, val in rng_set_dict.items():
                    if idx_set in val:
                        for y in ["adm", "rd", "r"]:
                            create_group_acl(test_groups[key][y], testset, y)
                        create_user_acl(test_users[key]["nogrp"], testset)

                # Generate random samples for level below
                rng_file_dict = {
                    "1": [80],
                    "25": list(range(0, 25)),
                    "50": list(range(0, 50)),
                    "75": list(range(0, 75)),
                }

                sys.stderr.write("Dataset " + str(idx_set + 1) + " created...\n")
                sys.stderr.write("Creating Datafiles...\n")

                # Create the datafiles
                for idx_file in range(100):
                    test_filename = "STRESSTEST_" + hundred_words[idx_file]
                    testfile = DataFile(
                        filename=test_filename, dataset=testset, size=42, md5sum="bogus"
                    )
                    testfile.save()
                    # Create ACL for "owner"
                    create_owner_acl(user, testfile)
                    # Create parameterset and parameters for datafile
                    parset = DatafileParameterSet(
                        schema=test_schema_file, datafile=testfile
                    )
                    parset.save()
                    for paramname in test_parnames["datafile"].values():
                        df_parameter = DatafileParameter(
                            name=paramname,
                            parameterset=parset,
                            string_value=paramname.name,
                        )
                        df_parameter.save()

                    # create ACLs for groups/users with 100% access
                    for y in ["adm", "rd", "r"]:
                        create_group_acl(test_groups["100"][y], testfile, y)
                    create_user_acl(test_users["100"]["nogrp"], testfile)
                    # if idx in random sample list, add acl for appropriate group/users
                    for key, val in rng_file_dict.items():
                        if idx_file in val:
                            for y in ["adm", "rd", "r"]:
                                create_group_acl(test_groups[key][y], testfile, y)
                            create_user_acl(test_users[key]["nogrp"], testfile)

                    sys.stderr.write("Datafile " + str(idx_file + 1) + " created...\n")
