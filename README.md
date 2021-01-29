# Motivation
At the beginning of each semester, course coordinators have to plan the
timetable for tutors for their courses. This is mostly done manually and
is very time-consuming. This project aims to automate that process, thus
saving time and effort of academic staff.

The following section lists the requirements for planning rosters for UQ
casual academic staff, specifically for EAIT tutors, but hopefully this
applies to tutors from other faculties as well.

# Model

## Situation

A timetable spans a number of **weeks** (e.g. Orientation Week, Week 1,
Week 2, SWOTVAC, etc.), each week has 7 **days** (i.e. Monday to
Sunday). The course coordinator also has to define **session streams**
at the beginning of a semester. A session stream runs in a number of
**weeks**. For example, session stream P01 runs from week 2 to week 13,
session stream P01e however, runs only during weeks 4, 5, 9, 11, 12.
Each session stream also runs during a specific time of a **day**. For
example, session streams P02 and P02e run from 10:00 to 12:00 on Monday.
A session stream also has a number of **tutors** who work on that
stream. Each session stream has a type, either 'practical' or
'tutorial'. In short, a session stream has to specify when it runs in a
week, a list of weeks that it runs in, the number of tutors that work on
it, and its type. Session streams can overlap, that is, two streams can
be run at the same time.

**Tutors** should be allocated to session streams and the allocation
should be the final output of this model. Before the allocation is
allocated, tutors have to input their **availabilities**, which are
essentially time slots when they're free in a week. For example, a tutor
is free from 10:00 to 15:00 and 16:00 to 18:00 on Tuesday, and 9:00 to
11:00 on Thursday. A tutor can be either 'new' or 'experienced'. A
session has to have at least 1 experienced tutor. A tutor also has a
preference that states if they want to work on either 'practical' or
'tutorial' sessions. A tutor can also specify the maximum number of
hours they want to work in a week, and the maximum number of continuous
hours they can work at once.

The goal of this model is to find an allocation that maximises spread
of the allocation, that is, minimises the variation of the number of
allocated hours between tutors. However, there's an
exception: the total number of allocated hours for each new tutor must
be less than or equal to half the total number of hours of an
experienced tutor. This threshold ratio can be changed. The value of
this threshold on the example specified above is 0.5. That is, a new
tutor works for half an hour on average for every hour an experienced
tutor has.
## Constraints
The following constraints have to be satisfied.
1. A tutor can only be allocated to sessions when they are free.
2. A tutor can only work on 1 session at a time.
3. If a tutor is allocated to a session stream, they have to work on
   every week that stream runs, at the time of that stream. For
   example, if P01 runs from 8:00 to 10:00 on Monday from weeks 1-13,
   then the tutors allocated to that stream are occupied during that
   time on Monday for those weeks.
4. The number of tutors allocated to a session has to match the
   **number of tutors** field of a session stream.
5. A tutor must not be allocated more hours than the maximum number of
   weekly hours they specified.
6. A tutor must not be allocated more contiguous hours than the
   maximum number of contiguous hours they
   specified.
7. There must be at least 1 experienced tutor allocated to each
   session.
8. On average, a new tutor must not work more than (the number of
   hours an experienced tutor has × a predefined.
9. The number of hours for the preferred type of session for a tutor
   has to be greater than or equal to (the total number of allocated
   hours × a predefined threshold). For example, if a tutor
   prefers to work on practical sessions to tutorial sessions, and the
   threshold is 0.6, then the number of hours allocated for practical
   sessions for that tutor must be greater than or equal to (0.6
   × total number of allocated hours).
# Setting up environment
## Prerequisites

1. Python 3.7 or above with the pip package manager is required. 
2. This project uses Gurobi, a mathematical optimisation engine. Gurobi can be downloaded 
 [here][4] (You will need to register an account). On Windows and Mac, you only need to
 install the executable/package. On Linux, you can follow [this guide][1].
4. [Request for an academic license for free][2] from Gurobi.
5. Keep track of your installation directory. It should typically be something like the following
 (replace `gurobi902` with the appropriate version of Gurobi you're using):
 * Windows: `C:\gurobi902\win64\ `.
 * MacOS: `/Library/gurobi902/mac64/`.
 * Linux: `/opt/gurobi902/linux64/`.

## Setting up
1. Clone this repo `git clone https://github.com/mike-fam/allocator.git` 
2. Create a new python virtual environment `cd allocator && python -m venv venv`
3. Activate the virtual environment `source venv/bin/activate`
4. Install the required Python packages `pip install -r requirements.txt`
6. Install Gurobi for your virtual environment:
```shell script
cd <installation-dir>  # Change <installation-dir> to the Gurobi directory as mentioned above
python setup.py install
```

## JSON IO format
The inputs and outputs of the solver is in the JSON format. The solver reads from a JSON file and
 outputs the results found to another JSON file. The input files are by default stored in `in/` 
 and `out/`.
 
### Input format
The JSON input string is an object with the following members.

#### Required
1. `request_time`: The time the request was received, in ISO 8061 format, e.g. `"2020-06-29T08:15
:27.243860"`
2. `requester`: The username that requested the allocation
2. `data`: Object containing the data of the timetable. This data will be used to create the
 model and generate the allocation. This object has the following properties.
    1. `days`: An array of **days** in a week, i.e. Monday to Sunday. Each _day_ has two properties,
     `id` and `name`.
        ```json
        [
            {"id": 1, "name": "Monday"},
            {"id": 2, "name": "Tuesday"},
            {"id":  3, "name": "Wednesday"}
        ]
        ```
    2. `weeks`: An array of **weeks** in a semester, e.g. O-Week, Week 1, Swotvac, etc. Each _week_
     has two properties, `id` and `name`.
        ```json
         [
             {"id": 1, "name": "O Week"},
             {"id": 2, "name": "Week 1"},
             {"id": 13, "name": "Swotvac"}
         ]
         ```
    3. `session_streams`: An array of **session streams**. A session stream represents a
     recurring session of a course, e.g P01, T02, etc. Each _session stream_ has the following
      properties:
        * `id`: The id of this session stream.
        * `name`: What this session stream is called, e.g. `"P01"`.
        * `type`: The type of this session stream, for now it's , either `"practical"` or
         `"tutorial"`.
        * `day`: The id of the day this stream runs on.
        * `time`: A **time slot** object specifying the start and end time of this session stream
        . A time slot object has 2 properties which are both integers, `start` and `end`.
        * `number_of_tutors`: The number of tutors this session stream requires.
        * `weeks`: An array of week ids this stream runs on.
        ```json
        [
            {
                "id": 12,
                "name": "P01",
                "number_of_tutors": 2,
                "time": {
                    "start": 8,
                    "end": 10
                },
                "type": "practical",
                "day": 1,
                "weeks": [66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81]
            },
            {
                "id": 13,
                "name": "P02",
                "number_of_tutors": 2,
                "time": {
                    "start": 10,
                    "end": 12
                },
                "type": "practical",
                "day": 1,
                "weeks": [66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81]
            }
        ]
        ```
    4. `tutors`: An array of **tutors**. A tutor is an object with the following properties:
        * `id`: The id of this tutor.
        * `name`: The name of this tutor.
        * `new`: `true` if the tutor is a new tutor, `false` otherwise.
        * `type_preference`: type of session this tutor wants to work on, either `"practical"` or
         `"tutorial"` or `null` if no preferences.
        * `max_contiguous_hours`: Maximum number of contiguous hours this tutor can take, as an int.
        * `max_weekly_hours`: Maximum number of weekly hours this tutor can take, as an int.
        * `availabilities`: Object mapping day ids to an array of **time slots** this tutor is free
         in.
        ```json
        [
            {
                "id": 1,
                "name": "John Smith",
                "new": true,
                "type_preference": "practical",
                "max_contiguous_hours": 4,
                "max_weekly_hours": 20,
                "availabilities": {
                    "1": [
                        {
                            "start": 8,
                            "end": 14
                        },
                        {
                            "start": 16,
                            "end": 19
                        }
                    ]
                }
            },
            {
                "id": 2,
                "name": "Jane Doe",
                "new": false,
                "type_preference": null,
                "max_contiguous_hours": 10,
                "max_weekly_hours": 40,
                "availabilities": {
                    "1": [
                        {
                            "start": 8,
                            "end": 10
                        }
                    ],
                    "4": [
                        {
                            "start": 12,
                            "end": 14
                        }
                    ]
                }
            }
        ]
        ```
       
#### Optional
The following properties are optional and don't need to be explicitly specified.
1. `new_threshold`: Threshold denoting the ratio of the total hours of a new tutor compare to the
 total hours of a senior tutor, as a float. For example, a threshold of 0.5 means on average, a
  new tutor works for half an hour for every hour an experienced tutor has. This threshold is 0.5
   by default.
2. `preference_thresholds`: An object with 2 keys, `"practical"` or `"tutorial"` denoting the
 ratio of the number of hours a tutor is allocated to their preferred session type. For example
 , if the ratio for practicals is 0.8, then if the tutor prefers to work in practicals, they will
  have **at least** 4 hours of practical for every 5 hours they get. This takes `{"practical": 0
  .8, "tutorial": 0.6}` as the default value. For this to work properly, all threshold values
   must be greater than 0.5.

### Output format

1. `status`:
    * code
    * type
    * message
2. `allocations`
3. `runtime`

### Filename convention

\<course code\>\_\<timetable_id\>\_\<index\>.json

[1]: https://www.gurobi.com/documentation/9.0/quickstart_linux/software_installation_guid.html#section:Installation
[2]: https://www.gurobi.com/downloads/end-user-license-agreement-academic/
[3]: https://bewisse.com/modheader/
[4]: http://www.gurobi.com/downloads/gurobi-optimizer
