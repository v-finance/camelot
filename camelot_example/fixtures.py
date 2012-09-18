import datetime
import StringIO
import os

def load_movie_fixtures():

    from camelot.model.fixture import Fixture
    from camelot.model.party import Person
    from camelot_example.model import Movie, VisitorReport
    from camelot.core.files.storage import Storage, StoredImage
    from camelot.core.resources import resource_filename

    storage = Storage(upload_to='covers',
                      stored_file_implementation = StoredImage)

    movies = [
        [
            u'The Shining',
            u'The tide of terror that swept America is here.',
            datetime.date(1980, 5, 23),
            (u'Stanley', u'Kubrick',),
            [
                u'Jack Nicholson',
                u'Shelley Duvall',
                u'Danny Lloyd',
                u'Scatman Crothers',
                u'Barry Nelson'
            ],
            [u'Horror',u'Mystery',u'Thriller'],
            u'thriller',
            4,
            u'shining.png',
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
            [
                u'Matt Damon',
                u'Franka Potente',
                u'Chris Cooper',
                u'Clive Owen',
                u'Brian Cox'
            ],
            [u'Action',u'Adventure'],
            u'action',
            4,
            u'bourne.png',
            u'A man is picked up by a fishing boat, bullet-riddled and without'
            ' memory, then races to elude assassins and recover from amnesia.'
        ],
        [
            u'Casino Royale',
            u'Discover how James became Bond.',
            datetime.date(2006, 11, 17),
            (u'Martin', u'Campbell'),
            [
                u'Daniel Craig',
                u'Eva Green',
                u'Mads Mikkelsen',
                u'Judi Dench',
                u'Jeffrey',
                u'Wright'
            ],
            [u'Action',u'Adventure'],
            u'action',
            5,
            u'casino.png',
            u"In his first mission, James Bond must stop Le Chiffre, a banker"
            " to the world's terrorist organizations, from winning a"
            " high-stakes poker tournament at Casino Royale in Montenegro."
        ],
        [
            u'Toy Story',
            u'Oooh...3-D.',
            datetime.date(1995, 11, 22),
            (u'John', u'Lasseter'),
            [
                u'Tom Hanks',
                u'Tim Allen',
                u'Don Rickles',
                u'Jim Varney',
                u'Wallace Shawn'
            ],
            [u'Animation',u'Adventure'],
            u'animation',
            4,
            u'toystory.png',
            u"a cowboy toy is profoundly threatened and jealous when a fancy"
            " spaceman toy supplants him as top toy in a boy's room."
        ],
        [
            u"Harry Potter and the Sorcerer's Stone",
            u'Let The Magic Begin.',
            datetime.date(2001, 11, 16),
            (u'Chris', u'Columbus'),
            [
                u'Richard Harris',
                u'Maggie Smith',
                u'Daniel Radcliffe',
                u'Fiona Shaw',
                u'Richard Griffiths'
            ],
            [u'Family',u'Adventure'],
            u'family',
            3,
            u'potter.png',
            u'Rescued from the outrageous neglect of his aunt and uncle, a'
            ' young boy with a great destiny proves his worth while attending'
            ' Hogwarts School of Witchcraft and Wizardry.'
        ],
        [
            u'Iron Man 2',
            u'The world now becomes aware of the dual life of the Iron Man.',
            datetime.date(2010, 5, 17),
            (u'Jon', 'Favreau'),
            [
                u'Robert Downey Jr.',
                u'Gwyneth Paltrow',
                u'Don Cheadle',
                u'Scarlett Johansson',
                u'Mickey Rourke'
            ],
            [u'Action',u'Adventure',u'Sci-fi'],
            u'sci-fi',
            3,
            u'ironman.png',
            u'billionaire Tony Stark must contend with deadly issues involving'
            ' the government, his own friends, as well as new enemies due to'
            ' his superhero alter ego Iron Man.'
        ],
        [
            u'The Lion King',
            u"Life's greatest adventure is finding your place in the Circle of"
            " Life.",
            datetime.date(1994, 6, 24),
            (u'Roger', 'Allers'),
            [
                u'Matthew Broderick',
                u'Jeremy Irons',
                u'James Earl Jones',
                u'Jonathan Taylor Thomas',
                u'Nathan Lane'
            ],
            [u'Animation',u'Adventure'],
            u'animation',
            5,
            u'lionking.png',
            u'Tricked into thinking he killed his father, a guilt ridden lion'
            ' cub flees into exile and abandons his identity as the future'
            ' King.'
        ],
        [
            u'Avatar',
            u'Enter the World.',
            datetime.date(2009, 12, 18),
            (u'James', u'Cameron'),
            [
                u'Sam Worthington',
                u'Zoe Saldana',
                u'Stephen Lang',
                u'Michelle Rodriguez',
                u'Sigourney Weaver'
            ],
            [u'Action',u'Adventure',u'Sci-fi'],
            u'sci-fi',
            5,
            u'avatar.png',
            u'A paraplegic marine dispatched to the moon Pandora on a unique'
            ' mission becomes torn between following his orders and'
            ' protecting the world he feels is his home.'
        ],
        [
            u'Pirates of the Caribbean: The Curse of the Black Pearl',
            u'Prepare to be blown out of the water.',
            datetime.date(2003, 7, 9),
            (u'Gore', u'Verbinski'),
            [
                u'Johnny Depp',
                u'Geoffrey Rush',
                u'Orlando Bloom',
                u'Keira Knightley',
                u'Jack Davenport'
            ],
            [u'Action',u'Adventure'],
            u'action',
            5,
            u'pirates.png',
            u"Blacksmith Will Turner teams up with eccentric pirate \"Captain\""
            " Jack Sparrow to save his love, the governor's daughter, from"
            " Jack's former pirate allies, who are now undead."
        ],
        [
            u'The Dark Knight',
            u'Why so serious?',
            datetime.date(2008, 7, 18),
            (u'Christopher', u'Nolan'),
            [
                u'Christian Bale',
                u'Heath Ledger',
                u'Aaron Eckhart',
                u'Michael Caine',
                u'Maggie Gyllenhaal'
            ],
            [u'Action',u'Drama'],
            u'action',
            5,
            u'darkknight.png',
            u'Batman, Gordon and Harvey Dent are forced to deal with the chaos'
            ' unleashed by an anarchist mastermind known only as the Joker, as'
            ' it drives each of them to their limits.'
        ]
    ]

    visits = {
        u'The Shining': [
            (u'Washington D.C.', 10000, datetime.date(1980, 5, 23)),
            (u'Buesnos Aires', 4000,datetime.date(1980, 6, 12)),
            (u'California', 13000,datetime.date(1980, 5, 23)),
        ],
        u'The Dark Knight': [
            (u'New York', 20000, datetime.date(2008, 7, 18)),
            (u'London', 15000, datetime.date(2008, 7, 20)),
            (u'Tokyo', 3000, datetime.date(2008, 7, 24)),
        ],
        u'Avatar': [
            (u'Shangai', 6000, datetime.date(2010, 1, 5)),
            (u'Atlanta', 3000, datetime.date(2009, 12, 18)),
            (u'Boston', 5000, datetime.date(2009, 12, 18)),
        ],
    }

    for title, short_description, releasedate, (director_first_name, director_last_name), cast, tags, genre, rating, cover, description in movies:
        director = Fixture.insert_or_update_fixture(
            Person,
            fixture_key = u'%s_%s'%(director_first_name, director_last_name),
            values = {'first_name':director_first_name,
                      'last_name':director_last_name}
        )
        movie = Fixture.find_fixture( Movie, title )
        if not movie:
            # use resource_filename, since resource_string seems to mess either with encoding
            # or with line endings, when on windows
            image = resource_filename( 'camelot_example', os.path.join( 'media', 'covers', cover ) )
            stored_image = storage.checkin( image )
            movie = Fixture.insert_or_update_fixture(
                Movie,
                fixture_key = title,
                values = {
                    'title': title,
                    'director':director,
                    'short_description':short_description,
                    'releasedate':releasedate,
                    'rating':rating,
                    'genre':genre,
                    'description':description,
                    'cover':stored_image,
                },
            )
        rep = visits.get(title, None)
        if rep:
            for city, visitors, date in rep:
                Fixture.insert_or_update_fixture(
                    VisitorReport,
                    fixture_key = '%s_%s' % (title, city),
                    values = {
                        'movie': movie,
                        'date': date,
                        'visitors': visitors,
                    }
                )
