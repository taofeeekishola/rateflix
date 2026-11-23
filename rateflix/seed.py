"""Demo data: real movies that use the posters and trailers already in the repo.

Run it with `flask --app rateflix seed-db`, or set SEED_DEMO_DATA=1 on Railway
so it runs when the app starts. It only ever adds data: a movie whose title
already exists is skipped, and genres, producers, studios and actors are
reused if one with the same name exists.
"""
from datetime import date

from rateflix.models import db, Movie, Genre, MovieGenre, Producer, Studio, Actor, MovieActor


MOVIES = [
    {
        'title': 'Bad Boys: Ride or Die',
        'released': date(2024, 6, 7),
        'description': "Miami detectives Mike Lowrey and Marcus Burnett set out to clear their late captain's "
                       "name after he is framed for working with the cartels, and end up wanted by the police "
                       "and the criminals alike.",
        'poster': '27f9a5249a624ee75b5b.jpg',
        'trailer': None,
        'producer': 'Jerry Bruckheimer',
        'studio': 'Columbia Pictures',
        'genres': ['Action', 'Comedy', 'Crime'],
        'cast': ['Will Smith', 'Martin Lawrence', 'Vanessa Hudgens', 'Eric Dane'],
    },
    {
        'title': '2012',
        'released': date(2009, 11, 13),
        'description': "As the Earth's crust starts to give way, setting off earthquakes, floods and eruptions "
                       "across the planet, a struggling novelist races to get his family to the ships secretly "
                       "built to survive the disaster.",
        'poster': '3a74de5b28cbd7942ca2.jpg',
        'trailer': 'f096b07788d4191b0912.mp4',
        'producer': 'Harald Kloser',
        'studio': 'Columbia Pictures',
        'genres': ['Action', 'Adventure', 'Sci-Fi'],
        'cast': ['John Cusack', 'Chiwetel Ejiofor', 'Amanda Peet', 'Woody Harrelson'],
    },
    {
        'title': 'M3GAN',
        'released': date(2023, 1, 6),
        'description': "A roboticist at a toy company builds a lifelike AI doll to look after her newly orphaned "
                       "niece, but the doll takes its job of protecting the girl much too far.",
        'poster': '79069e27252d9ccf67ef.jpg',
        'trailer': 'b88a432b891b6d8d4ecd.mp4',
        'producer': 'Jason Blum',
        'studio': 'Universal Pictures',
        'genres': ['Horror', 'Sci-Fi', 'Thriller'],
        'cast': ['Allison Williams', 'Violet McGraw', 'Amie Donald', 'Jenna Davis'],
    },
    {
        'title': 'A Quiet Place: Day One',
        'released': date(2024, 6, 28),
        'description': "On the day creatures that hunt by sound descend on New York City, Sam, a woman living "
                       "with a terminal illness, tries to cross the silent city with her cat and a frightened "
                       "law student.",
        'poster': '814c76987780760194bc.jpg',
        'trailer': '44e2e7d5ab1739403052.mp4',
        'producer': 'Michael Bay',
        'studio': 'Paramount Pictures',
        'genres': ['Horror', 'Sci-Fi', 'Thriller'],
        'cast': ["Lupita Nyong'o", 'Joseph Quinn', 'Alex Wolff', 'Djimon Hounsou'],
    },
    {
        'title': 'Dracula Untold',
        'released': date(2014, 10, 10),
        'description': "To save his family and his people from the invading Ottoman army, Prince Vlad Tepes "
                       "makes a desperate bargain for monstrous powers, knowing they come at a terrible price.",
        'poster': '874a14c5f2283d31a0c5.jpg',
        'trailer': '74aa379dd131a92afd91.mp4',
        'producer': 'Michael De Luca',
        'studio': 'Universal Pictures',
        'genres': ['Action', 'Fantasy', 'Horror'],
        'cast': ['Luke Evans', 'Sarah Gadon', 'Dominic Cooper', 'Charles Dance'],
    },
    {
        'title': 'Nope',
        'released': date(2022, 7, 22),
        'description': "A brother and sister who train horses for Hollywood notice something unexplained in the "
                       "clouds above their ranch in inland California, and decide to catch it on camera.",
        'poster': '9153efc1a6376b5d7724.jpg',
        'trailer': '94a5509601e74256d8b9.mp4',
        'producer': 'Jordan Peele',
        'studio': 'Universal Pictures',
        'genres': ['Horror', 'Mystery', 'Sci-Fi'],
        'cast': ['Daniel Kaluuya', 'Keke Palmer', 'Steven Yeun', 'Brandon Perea'],
    },
    {
        'title': 'Maharaja',
        'released': date(2024, 6, 14),
        'description': "A soft-spoken barber walks into a police station to report a theft from his home: a "
                       "dustbin. His odd determination to get it back opens up a far darker story.",
        'poster': 'a9e6cdfca33fe9e5e13e.jpg',
        'trailer': '8a8588eb9e80ee6a244e.mp4',
        'producer': 'Sudhan Sundaram',
        'studio': 'Passion Studios',
        'genres': ['Action', 'Crime', 'Drama'],
        'cast': ['Vijay Sethupathi', 'Anurag Kashyap', 'Mamta Mohandas', 'Natarajan Subramaniam'],
    },
    {
        'title': 'Damsel',
        'released': date(2024, 3, 8),
        'description': "A young woman agrees to marry the prince of a rich kingdom, then learns she has been "
                       "chosen as an offering to a dragon and has to fight her way out of its cave.",
        'poster': 'b0994ed6d0a52b2dccf5.jpg',
        'trailer': 'da1eeba6e4e26a0a51ea.mp4',
        'producer': 'Joe Roth',
        'studio': 'Netflix',
        'genres': ['Action', 'Adventure', 'Fantasy'],
        'cast': ['Millie Bobby Brown', 'Ray Winstone', 'Angela Bassett', 'Robin Wright'],
    },
    {
        'title': 'Ghost in the Shell',
        'released': date(2017, 3, 31),
        'description': "In a future city where people upgrade their bodies with cybernetics, the Major, a human "
                       "mind in a fully synthetic body, leads an elite unit hunting a hacker who targets the "
                       "company that built her.",
        'poster': 'b648998ba973036a58b4.jpg',
        'trailer': '8c298a100caf0f6f0a24.mp4',
        'producer': 'Avi Arad',
        'studio': 'Paramount Pictures',
        'genres': ['Action', 'Sci-Fi', 'Thriller'],
        'cast': ['Scarlett Johansson', 'Pilou Asbæk', 'Takeshi Kitano', 'Juliette Binoche'],
    },
    {
        'title': 'Alien: Romulus',
        'released': date(2024, 8, 16),
        'description': "Young colonists desperate to leave their bleak mining planet salvage parts from a "
                       "derelict space station, and wake something deadly that has been waiting on board.",
        'poster': 'seed-alien-romulus.jpg',
        'trailer': None,
        'producer': 'Ridley Scott',
        'studio': '20th Century Studios',
        'genres': ['Horror', 'Sci-Fi', 'Thriller'],
        'cast': ['Cailee Spaeny', 'David Jonsson', 'Archie Renaux', 'Isabela Merced'],
    },
    {
        'title': 'Deadpool & Wolverine',
        'released': date(2024, 7, 26),
        'description': "Pulled back into action by an agency that polices the multiverse, Deadpool recruits a "
                       "very reluctant version of Wolverine to stop his whole world from being wiped out.",
        'poster': 'seed-deadpool-and-wolverine.jpg',
        'trailer': None,
        'producer': 'Kevin Feige',
        'studio': 'Marvel Studios',
        'genres': ['Action', 'Adventure', 'Comedy'],
        'cast': ['Ryan Reynolds', 'Hugh Jackman', 'Emma Corrin', 'Matthew Macfadyen'],
    },
    {
        'title': 'Despicable Me 4',
        'released': date(2024, 7, 3),
        'description': "Gru, Lucy and the girls go into hiding under new identities when an old rival escapes "
                       "from prison looking for revenge, just as Gru is getting used to life with baby Gru Jr.",
        'poster': 'seed-despicable-me-4.jpg',
        'trailer': None,
        'producer': 'Chris Meledandri',
        'studio': 'Illumination',
        'genres': ['Animation', 'Comedy', 'Family'],
        'cast': ['Steve Carell', 'Kristen Wiig', 'Will Ferrell', 'Joey King'],
    },
    {
        'title': 'Dìdi',
        'released': date(2024, 7, 26),
        'description': "In the summer of 2008, a 13-year-old Taiwanese American boy in Fremont, California, "
                       "fumbles through friendships, first crushes, skate videos and family tension in the "
                       "last weeks before high school.",
        'poster': 'seed-didi.jpg',
        'trailer': None,
        'producer': 'Carlos López Estrada',
        'studio': 'Focus Features',
        'genres': ['Comedy', 'Drama'],
        'cast': ['Izaac Wang', 'Joan Chen', 'Shirley Chen', 'Chang Li Hua'],
    },
    {
        'title': 'Fly Me to the Moon',
        'released': date(2024, 7, 12),
        'description': "In the middle of the 1960s space race, a slick marketing specialist hired to sell NASA "
                       "to the public clashes with the launch director, then is asked to stage a fake Moon "
                       "landing as a backup plan.",
        'poster': 'seed-fly-me-to-the-moon.jpg',
        'trailer': None,
        'producer': 'Scarlett Johansson',
        'studio': 'Apple Original Films',
        'genres': ['Comedy', 'Drama', 'Romance'],
        'cast': ['Scarlett Johansson', 'Channing Tatum', 'Woody Harrelson', 'Ray Romano'],
    },
    {
        'title': 'Gladiator II',
        'released': date(2024, 11, 22),
        'description': "Years after the death of Maximus, Lucius is captured when Rome conquers his home and is "
                       "forced to fight in the Colosseum, where he sets his sights on the emperors who rule "
                       "the city.",
        'poster': 'seed-gladiator-ii.jpg',
        'trailer': None,
        'producer': 'Ridley Scott',
        'studio': 'Paramount Pictures',
        'genres': ['Action', 'Adventure', 'Drama'],
        'cast': ['Paul Mescal', 'Pedro Pascal', 'Denzel Washington', 'Connie Nielsen', 'Joseph Quinn'],
    },
    {
        'title': 'Inside Out 2',
        'released': date(2024, 6, 14),
        'description': "As Riley turns thirteen, Joy, Sadness, Anger, Fear and Disgust suddenly have to share "
                       "headquarters with a group of new emotions, led by Anxiety, who has her own plans for "
                       "Riley.",
        'poster': 'seed-inside-out-2.jpg',
        'trailer': None,
        'producer': 'Mark Nielsen',
        'studio': 'Pixar Animation Studios',
        'genres': ['Animation', 'Comedy', 'Family'],
        'cast': ['Amy Poehler', 'Maya Hawke', 'Kensington Tallman', 'Ayo Edebiri'],
    },
    {
        'title': 'Longlegs',
        'released': date(2024, 7, 12),
        'description': "An FBI agent with uncanny instincts is put on a string of unsolved family murders linked "
                       "by coded letters, and the case turns out to be closer to her than she realises.",
        'poster': 'seed-longlegs.jpg',
        'trailer': None,
        'producer': 'Nicolas Cage',
        'studio': 'Neon',
        'genres': ['Crime', 'Horror', 'Mystery'],
        'cast': ['Maika Monroe', 'Nicolas Cage', 'Blair Underwood', 'Alicia Witt'],
    },
    {
        'title': 'My Spy: The Eternal City',
        'released': date(2024, 7, 18),
        'description': "CIA agent JJ tags along on Sophie's high school choir trip to Italy, and the two get "
                       "caught up in a nuclear plot aimed at Vatican City.",
        'poster': 'seed-my-spy-the-eternal-city.jpg',
        'trailer': None,
        'producer': 'Chris Bender',
        'studio': 'Amazon MGM Studios',
        'genres': ['Action', 'Comedy'],
        'cast': ['Dave Bautista', 'Chloe Coleman', 'Kristen Schaal', 'Ken Jeong'],
    },
    {
        'title': 'The Beast Within',
        'released': date(2024, 7, 26),
        'description': "Ten-year-old Willow secretly follows her parents on one of their mysterious night trips "
                       "from their remote farmhouse into the woods, and starts to uncover what her family has "
                       "been hiding.",
        'poster': 'seed-the-beast-within.jpg',
        'trailer': None,
        'producer': 'Alex Chang',
        'studio': 'Paradox House',
        'genres': ['Drama', 'Horror', 'Thriller'],
        'cast': ['Kit Harington', 'Ashleigh Cummings', 'Caoilinn Springall', 'James Cosmo'],
    },
]


def _get_or_create(model, field, name):
    ## reuse a row with the same name (e.g. a genre an admin already added) instead of duplicating it
    row = model.query.filter(getattr(model, field) == name).first()
    if row is None:
        row = model(**{field: name})
        db.session.add(row)
        db.session.flush()
    return row


def seed_demo_data():
    ## adds the movies above; returns how many were new
    added = 0
    for data in MOVIES:
        if Movie.query.filter_by(movie_title=data['title']).first():
            continue

        producer = _get_or_create(Producer, 'producer_name', data['producer'])
        studio = _get_or_create(Studio, 'studio_name', data['studio'])

        movie = Movie(
            movie_title=data['title'],
            movie_release_date=data['released'],
            movie_description=data['description'],
            movie_poster=data['poster'],
            movie_trailer=data['trailer'],
            movie_status='approved',
            producer_id=producer.producer_id,
            production_studio=studio.studio_id,
        )
        db.session.add(movie)
        db.session.flush()

        for name in data['genres']:
            genre = _get_or_create(Genre, 'genre_name', name)
            db.session.add(MovieGenre(movie_id=movie.movie_id, genre_id=genre.genre_id))

        for name in data['cast']:
            actor = _get_or_create(Actor, 'actor_name', name)
            db.session.add(MovieActor(movie_id=movie.movie_id, actor_id=actor.actor_id))

        added += 1

    db.session.commit()
    return added
