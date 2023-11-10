#  ============================================================================
#
#  Copyright (C) 2007-2016 Conceptive Engineering bvba.
#  www.conceptive.be / info@conceptive.be
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are met:
#      * Redistributions of source code must retain the above copyright
#        notice, this list of conditions and the following disclaimer.
#      * Redistributions in binary form must reproduce the above copyright
#        notice, this list of conditions and the following disclaimer in the
#        documentation and/or other materials provided with the distribution.
#      * Neither the name of Conceptive Engineering nor the
#        names of its contributors may be used to endorse or promote products
#        derived from this software without specific prior written permission.
#  
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
#  ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
#  WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#  DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
#  DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
#  (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
#  LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#  ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#  (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
#  ============================================================================
import datetime

from sqlalchemy import insert

from camelot.model.party import Person, Party
from camelot_example.model import Movie, Tag

def load_movie_fixtures(connection):

    connection.execute(insert(Party.__table__),[
        {"id": 1, "row_type": "person",},
        {"id": 2, "row_type": "person",},
        {"id": 3, "row_type": "person",},
        {"id": 4, "row_type": "person",},
        {"id": 5, "row_type": "person",},
        ],)

    connection.execute(insert(Person.__table__),[
        {"id": 1, "first_name": "Stanley", "last_name": "Kubrick"},
        {"id": 2, "first_name": "Doug", "last_name": "Liman"},
        {"id": 3, "first_name": "Martin", "last_name": "Campbell"},
        {"id": 4, "first_name": "John", "last_name": "Lasseter"},
        {"id": 5, "first_name": "Chris", "last_name": "Columbus"},
        ],)

    connection.execute(insert(Movie.__table__),[
        {
            "title": 'The Shining',
            "short_description": 'The tide of terror that swept America is here.',
            "releasedate": datetime.date(1980, 5, 23),
            "director_id": 1,
            "genre": 'thriller',
            "rating": 4,
            "description": 'A family heads to an isolated hotel for the winter where an evil'
            ' and spiritual presence influences the father into violence,'
            ' while his psychic son sees horrific forebodings from the past'
            ' and of the future.'
        }, {
            "title": 'The Bourne Identity',
            "short_description": 'Matt Damon is Jason Bourne.',
            "releasedate": datetime.date(2002, 6, 14),
            "director_id": 2,
            "genre": 'action',
            "rating": 4,
            "description": 'A man is picked up by a fishing boat, bullet-riddled and without'
            ' memory, then races to elude assassins and recover from amnesia.'
        }, {
            "title": 'Casino Royale',
            "short_description": 'Discover how James became Bond.',
            "releasedate": datetime.date(2006, 11, 17),
            "director_id": 3,
            "genre": 'action',
            "rating": 5,
            "description": "In his first mission, James Bond must stop Le Chiffre, a banker"
            " to the world's terrorist organizations, from winning a"
            " high-stakes poker tournament at Casino Royale in Montenegro."
        }, {
            "title": 'Toy Story',
            "short_description": 'Oooh...3-D.',
            "releasedate": datetime.date(1995, 11, 22),
            "director_id": 4,
            "genre": 'animation',
            "rating": 4,
            "description": "a cowboy toy is profoundly threatened and jealous when a fancy"
            " spaceman toy supplants him as top toy in a boy's room."
        }, {
            "title": "Harry Potter and the Sorcerer's Stone",
            "short_description": 'Let The Magic Begin.',
            "releasedate": datetime.date(2001, 11, 16),
            "director_id": 5,
            "genre": 'family',
            "rating": 3,
            "description": 'Rescued from the outrageous neglect of his aunt and uncle, a'
            ' young boy with a great destiny proves his worth while attending'
            ' Hogwarts School of Witchcraft and Wizardry.'
        },
    ])

    connection.execute(insert(Tag.__table__),[
        {"id": 1, "name": "Drama",},
        ],)
