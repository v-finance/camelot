"""
test ordering options
"""

from . import TestMetaData

from camelot.core.orm import ( Field, ManyToMany, ManyToOne, OneToMany, using_options,
                               has_field, has_many, belongs_to, options,
                               has_and_belongs_to_many, options_defaults )

from sqlalchemy.types import String, Unicode, Integer

class TestOrderBy( TestMetaData ):
    
    def setUp( self ):
        super( TestOrderBy, self ).setUp()
    
        class Record( self.Entity ):
            title = Field(String(100))
            year = Field(Integer)
            artist = ManyToOne('Artist')
            genres = ManyToMany('Genre')
    
            # order titles descending by year, then by title
            using_options(order_by=['-year', 'title'])
    
            def __str__(self):
                return "%s - %s (%d)" % (self.artist.name, self.title, self.year)
    
        class Artist( self.Entity ):
            name = Field(String(30))
            records = OneToMany('Record', order_by=['year', '-title'])
    
        class Genre( self.Entity ):
            name = Field(String(30))
            records = ManyToMany('Record', order_by='-title')
    
        self.create_all()
        self.Record = Record
        self.Artist = Artist
        self.Genre = Genre
    
        # insert some data
        with self.session.begin():
            artist = Artist(name="Dream Theater")
            genre = Genre(name="Progressive metal")
            titles = (
                ("A Change Of Seasons", 1995),
                ("Awake", 1994),
                ("Falling Into Infinity", 1997),
                ("Images & Words", 1992),
                ("Metropolis Pt. 2: Scenes From A Memory", 1999),
                ("Octavarium", 2005),
                # 2005 is a mistake to make the test more interesting
                ("Six Degrees Of Inner Turbulence", 2005),
                ("Train Of Thought", 2003),
                ("When Dream And Day Unite", 1989)
            )
        
            for title, year in titles:
                Record(title=title, artist=artist, year=year, genres=[genre])
    
        self.session.expire_all()
    
    def test_mapper_order_by(self):
        records = self.Record.query.all()

        assert records[0].year == 2005
        assert records[2].year >= records[5].year
        assert records[3].year >= records[4].year
        assert records[-1].year == 1989

    def test_o2m_order_by(self):
        records = self.Artist.get_by(name="Dream Theater").records

        assert records[0].year == 1989
        assert records[2].year <= records[5].year
        assert records[3].year <= records[4].year
        assert records[-1].title == 'Octavarium'
        assert records[-1].year == 2005

    def test_m2m_order_by(self):
        records = self.Genre.get_by(name="Progressive metal").records

        assert records[0].year == 1989
        assert records[2].title >= records[5].title
        assert records[3].title >= records[4].title
        assert records[-1].year == 1995

