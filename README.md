Osmada − OpenStreetMap Augmented Diff Analyzer
==============================================

[![Build Status](https://travis-ci.org/Cartocite/osmada.svg?branch=master)](https://travis-ci.org/Cartocite/osmada)

Introduction
------------
Osmada is a component to help monitor changes to OSM data. Unlike most QA Tools that are
based on monitoring changesets, OSMADA is designed to help monitor changes to data you're
interested in, for instance the shops and restaurants of your city.

Osmada reads and analyzes the result of
[Overpass Augmented Diff](https://wiki.openstreetmap.org/wiki/Overpass_API/Augmented_Diffs) (*adiff*)
requests in a database, it can then apply filters on those diffs and export the filtered diffs in various
formats. The intention is to filter out changes one wants to ignore and produce a report with
the significant changes. This report can then be used by a mapper to check individual changes.

An Augmented diff request produces an XML response composed of `<action>` elements. There are 3 types
of actions : create, modify, delete. Each action contains two elements, the `<old>` and the `<new>`
versions of the same OSM object. Osmada analyzes those changes, loads them in a database and augments
each change with information such as main tags, added and modified tags. Osmada can then filter the
changes, and export the filtered changes in the same format or a different one.

Osmada is designed to be used in workflows, typically composed of 3 steps :
1. Load the changes in a database (SpatiaLite)
2. Filter changes, for instance to ignore changes from trusted users or changes to unsignificant tags
3. Export the remaining changes in same format (Augmented diff) or a different one (CSV only for now)

A workflow is defined as a Python settings file, a [commented example](osmada/local_settings.py.example) is supplied in the osmada folder.


Installing
----------

The most convenient is to use a Python virtualenv.

### Install virtualenv itself

eg ; on Debian-like :

    $ sudo apt install python3 virtualenv \
      spatialite-bin libsqlite3-mod-spatialite libproj-dev gdal-bin

### Create the virtualenv
On Windows

    $ mkvirtualenv --python=/usr/bin/python3 ./venv

On Ubuntu

    $ virtualenv --python=/usr/bin/python3 ./venv


### Enter the virtualenv

Be sure to be inside the venv before running any osmada command or install
dependencies. To enter the venv :

    $ source venv/bin/activate

Notice the `(venv)` at the beggining on your shell prompt.

### Install the dependencies

    (venv) $ pip install -r requirements.txt


Create the database :

    $ ./manage.py migrate

You're good to go !


Using it
--------

### Commands

*osmada* is mainly a CLI tool.

They are defined as django commands ; thus they run as:

    $ ./manage.py <command name>

To get command list:

    $ ./manage.py help

Get help about a specific command:

    $ ./manage.py help <command name>

### Running workflows

Workflows are the complete transformation process :

1. Load diff data from an external source into DB.
2. Apply one or several filters
3. Output as string in a given format

You can have different workflows, configured in settings. By default, you only
have one available called `passthrough` (basically useless) ; you can run it on
some adiff file of yours:

    $ ./manage.py workflow passthrough \
        --input-paths /home/steve/my_adiff.xml

It will output adiff XML code to stdout ; you may want to redirect it to some
file:

    $ ./manage.py workflow passthrough --input-paths
        /home/steve/my_adiff.xml > out_adiff.xml


Alternatively, you can mention `--output-paths` :

    $ ./manage.py workflow passthrough
        --input-paths /home/steve/my_adiff.xml \
        --output-paths out_adiff.xml

*workflow* and *loaddata* commands can be made more verbose, using `LOGLEVEL`
environment variable. Eg:

    $ LOGLEVEL=DEBUG ./manage.py workflow passthrough \
        --input-paths /home/steve/my_adiff.xml > out_adiff.xml

Available log levels are : *INFO*, *DEBUG*, *WARNING*, *ERROR* and *CRITICAL*. Default is **INFO**.

### Loading data

You may want to load data into the DB without applying an entire workflow.

    $ ./manage.py import_adiff /home/steve/my_adiff.xml


### Using web interface

There is a web interface to interactively visualize data in DB.

You first create a user:

    $ ./manage.py createsuperuser

Then you can run the local webserver


    $ ./manage.py runserver


And fire your browser to http://localhost:8000/admin

### Flushing the db

Each time you run a workflow or import data, the database fills up ; if you
want to cleanup all that :

    $ ./manage.py flush


Configuration
-------------

Default settings are stored in *osmada/settings.py* ; do not edit this
file.

To start overriding settings :

    $ cp osmada/local_settings.py.example osmada/local_settings.py

And edit *osmada/local_settings.py* to suit your needs ; the example file
is commented and used to document the setting keys.

### Storing lists in separate files

Some settings, such as `TRUSTED_USERS` are lists. You may want to store them
into flat files (one value/line) within *osmada/settings.d* folder.

Here is an example with `TRUSTED_USERS` defined in a flat file.

1. Create the *osmada/settings.d/trusted_users.list* file containing one value
   per line (empty lines are ignored) e.g:
   ```
   margaret doe
   thelma doe
   john doe
   jack doe
   ```

1. Add this line (once) at the beggining of your *local_settings.py*:
    ```
    from .utils import flat_file_list
    ```

2. Reference  the flat file from your *local_settings.py*
    ```
    TRUSTED_USERS = flat_file_list('settings.d/trusted_users.list')
    ```

Upgrade to the latest version
------------------------------

Be sure to have the venv activated.

Pull latest code from git:

    $ git pull

Install latest requirements:

    $ pip install -r requirements.txt

Apply latest database migrations:

    $ ./manage.py migrate

You're good to go :-)

additionaly, dependencies may have evolved after update, so if something yells,
you may want to do *apt* and *pip* steps from [Installing section](#installing)
again.


Advanced
--------

### Running unit tests

Hint : run them each time you modify the code, and better: add tests for your
code.

Initial setup:

    $ pip install -r test-requirements.txt

Run tests:

    $ pytest

See coverage:

    $ coverage run manage.py test --settings=osmada.base_settings
    $ coverage report

### How long does my workflow takes ?

Use the `time` command to figure out.

    $ time ./manage.py workflow ...

### Use with cron / scripts

To call *manage.py* commands from cron or shell scripts ; you may want to write
something like:

    /path/to/your/venv/bin/python /path/to/your/manage.py command ...

### What about treating a whole folder of adiff ?

Bash to the rescue (example) :

    $ for f in /home/steve/*.osm; do ./manage.py workflow passthrough --input-paths "$f" --ouptput-paths "/tmp/`basename -s.osm ${f}`.adiff" ; done
