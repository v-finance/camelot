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

def load_movie_fixtures(session):

    from camelot.model.party import Person
    from camelot_example.model import Movie, Tag

    movies = [
        [
            u'The Shining',
            u'The tide of terror that swept America is here.',
            datetime.date(1980, 5, 23),
            (u'Stanley', u'Kubrick',),
            u'thriller',
            4,
            u'A family heads to an isolated hotel for the winter where an evil'
            ' and spiritual presence influences the father into violence,'
            ' while his psychic son sees horrific forebodings from the past'
            ' and of the future.'
        ],
        [
            u'The Bourne Identity',
            u'Matt Damon is Jason Bourne.',
            datetime.date(2002, 6, 14),
            (u'Doug', u'Liman'),
            u'action',
            4,
            u'A man is picked up by a fishing boat, bullet-riddled and without'
            ' memory, then races to elude assassins and recover from amnesia.'
        ],
        [
            u'Casino Royale',
            u'Discover how James became Bond.',
            datetime.date(2006, 11, 17),
            (u'Martin', u'Campbell'),
            u'action',
            5,
            u"In his first mission, James Bond must stop Le Chiffre, a banker"
            " to the world's terrorist organizations, from winning a"
            " high-stakes poker tournament at Casino Royale in Montenegro."
        ],
        [
            u'Toy Story',
            u'Oooh...3-D.',
            datetime.date(1995, 11, 22),
            (u'John', u'Lasseter'),
            u'animation',
            4,
            u"a cowboy toy is profoundly threatened and jealous when a fancy"
            " spaceman toy supplants him as top toy in a boy's room."
        ],
        [
            u"Harry Potter and the Sorcerer's Stone",
            u'Let The Magic Begin.',
            datetime.date(2001, 11, 16),
            (u'Chris', u'Columbus'),
            u'family',
            3,
            u'Rescued from the outrageous neglect of his aunt and uncle, a'
            ' young boy with a great destiny proves his worth while attending'
            ' Hogwarts School of Witchcraft and Wizardry.'
        ],
        [
            u'Iron Man 2',
            u'The world now becomes aware of the dual life of the Iron Man.',
            datetime.date(2010, 5, 17),
            (u'Jon', 'Favreau'),
            u'sci-fi',
            3,
            u'billionaire Tony Stark must contend with deadly issues involving'
            ' the government, his own friends, as well as new enemies due to'
            ' his superhero alter ego Iron Man.'
        ],
        [
            u'The Lion King',
            u"Life's greatest adventure is finding your place in the Circle of"
            " Life.",
            datetime.date(1994, 6, 24),
            (u'Roger', u'Allers'),
            u'animation',
            5,
            u'Tricked into thinking he killed his father, a guilt ridden lion'
            ' cub flees into exile and abandons his identity as the future'
            ' King.'
        ],
        [
            u'Avatar',
            u'Enter the World.',
            datetime.date(2009, 12, 18),
            (u'James', u'Cameron'),
            u'sci-fi',
            5,
            u'A paraplegic marine dispatched to the moon Pandora on a unique'
            ' mission becomes torn between following his orders and'
            ' protecting the world he feels is his home.'
        ],
        [
            u'Pirates of the Caribbean: The Curse of the Black Pearl',
            u'Prepare to be blown out of the water.',
            datetime.date(2003, 7, 9),
            (u'Gore', u'Verbinski'),
            u'action',
            5,
            u"Blacksmith Will Turner teams up with eccentric pirate \"Captain\""
            " Jack Sparrow to save his love, the governor's daughter, from"
            " Jack's former pirate allies, who are now undead."
        ],
        [
            u'The Dark Knight',
            u'Why so serious?',
            datetime.date(2008, 7, 18),
            (u'Christopher', u'Nolan'),
            u'action',
            5,
            u'Batman, Gordon and Harvey Dent are forced to deal with the chaos'
            ' unleashed by an anarchist mastermind known only as the Joker, as'
            ' it drives each of them to their limits.'
        ]
    ]

    Tag(name='Drama', _session=session)

    for title, short_description, releasedate, (director_first_name, director_last_name), genre, rating, description in movies:
        director = Person(
            first_name=director_first_name,
            last_name=director_last_name,
            _session=session,
        )
        Movie(
            title=title,
            director=director,
            short_description=short_description,
            releasedate=releasedate,
            rating=rating,
            genre=genre,
            description=description,
            _session=session, 
        )
            
    session.flush()
