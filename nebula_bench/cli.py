# -*- coding: utf-8 -*-
import click

from nebula_bench import setting
from nebula_bench.utils import logger
from nebula_bench.controller import NebulaController
from nebula_bench.utils import run_process

SH_COMMAND = '/bin/bash'


def common(f):
    f = click.option("-f", "--folder", help="ldbc data folder, default: target/data/test_data")(f)

    f = click.option("-a", "--address", help="Nebula Graph address, default: 127.0.0.1:9669")(f)
    f = click.option("-u", "--user", help="Nebula Graph address, default: root")(f)
    f = click.option("-p", "--password", help="Nebula Graph address, default: nebula")(f)
    f = click.option(
        "-s",
        "--space",
        help="Nebula Graph address, default: stress_test_{current_date}",
    )(f)

    return f


@click.group()
def cli():
    pass


@cli.command(help="generate and split ldbc data")
@click.option("-s", "--scale-factor", default="1", help="scale factor for ldbc, default: 1")
@click.option("-og", "--only-generate", default=False, is_flag=True, help="only generate data")
@click.option(
    "-os",
    "--only-split",
    default=False,
    is_flag=True,
    help="only split data in target/data/test_data",
)
def data(scale_factor, only_generate, only_split):
    my_env = {"scaleFactor": str(scale_factor)}
    if only_generate:
        command = [SH_COMMAND, setting.WORKSPACE_PATH / "scripts/generate-data.sh"]
        run_process(command, my_env)
        return
    elif only_split:
        command = [SH_COMMAND, setting.WORKSPACE_PATH / "scripts/split-data.sh"]
        run_process(command)
    else:
        command = [SH_COMMAND, setting.WORKSPACE_PATH / "scripts/generate-data.sh"]
        run_process(command, my_env)
        command = [SH_COMMAND, setting.WORKSPACE_PATH / "scripts/split-data.sh"]
        run_process(command)


@cli.group(help="operation for nebula graph")
def nebula():
    pass


@nebula.command(help="clean the nebula space data")
@click.option("-a", "--address", help="Nebula Graph address, default: 127.0.0.1:9669")
@click.option("-u", "--user", help="Nebula Graph address, default: root")
@click.option("-p", "--password", help="Nebula Graph address, default: nebula")
@click.option("-k", "--keep", help="keep spaces that not be dropped, e.g. space1,space2")
def clean(address, user, password, keep):
    sc = NebulaController(user=user, password=password, address=address)
    value = click.confirm("Will delete all spaces in Nebula Graph. Continue?", abort=True)
    sc.clean_spaces(keep)


@nebula.command(help="import the data")
@common
@click.option(
    "-t",
    "--vid-type",
    default="int",
    help="space vid type, values should be [int, string], default: int",
)
@click.option(
    "-d",
    "--dry-run",
    default=False,
    is_flag=True,
    help="Dry run, just dump the import config file, default: False",
)
def importer(folder, address, user, password, space, vid_type, dry_run):
    assert vid_type in ["int", "string"], 'the vid type should be "ini" or "string" '
    nc = NebulaController(folder, space, user, password, address, vid_type)
    nc.importer_space(dry_run)
    if not dry_run:
        click.echo("begin space compact")
        nc.compact()
        click.echo("end space compact")
    nc.release()


# @nebula.command(help="initial nebula graph, including create indexes")
# @common
# def init(folder, address, user, password, space):
#     nc = NebulaController(
#         data_folder=folder,
#         user=user,
#         password=password,
#         address=address,
#         space=space,
#         vid_type="int",
#     )

#     nc.init_space()


# @cli.group()
# def stress():
#     pass
