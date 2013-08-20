import logging
from flask.ext.script import Manager
from mptracker.scraper.common import get_cached_session
from mptracker import models
from mptracker.common import TablePatcher, fix_local_chars

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

scraper_manager = Manager()


@scraper_manager.command
def questions(year='2013'):
    from mptracker.scraper.questions import QuestionScraper

    patcher = TablePatcher(models.Question,
                           models.db.session,
                           key_columns=['number', 'date'])

    person_matcher = models.PersonMatcher()

    def get_questions():
        questions_scraper = QuestionScraper(get_cached_session())
        for question in questions_scraper.run(year):
            person = person_matcher.get_person(question.person_name,
                                               question.person_cdep_id,
                                               strict=True)
            q_data = {
                'number':    question.number,
                'type':      question.q_type,
                'method':    question.method,
                'title':     question.title,
                'url':       question.url,
                'pdf_url':   question.pdf_url,
                'addressee': '; '.join(question.addressee),
                'date':      question.date,
                'person_id': person.id,
            }
            yield q_data

    patcher.update(get_questions())


@scraper_manager.command
def people(year='2012'):
    from mptracker.scraper.people import PersonScraper

    patcher = TablePatcher(models.Person,
                           models.db.session,
                           key_columns=['cdep_id'])

    def get_people():
        person_scraper = PersonScraper(get_cached_session())
        for row in person_scraper.fetch_people(year):
            county_name = row.pop('county_name')
            if county_name:
                ok_name = fix_local_chars(county_name.title())
                if ok_name == "Bistrița-Năsăud":
                    ok_name = "Bistrița Năsăud"
                county = models.County.query.filter_by(name=ok_name).first()
                if county is None:
                    logger.warn("Can't match county name %r", ok_name)
                else:
                    row['county'] = county

            yield row

    patcher.update(get_people())


@scraper_manager.command
def committee_summaries(year=2013):
    from mptracker.scraper.committee_summaries import SummaryScraper

    patcher = TablePatcher(models.CommitteeSummary,
                           models.db.session,
                           key_columns=['pdf_url'])

    summary_scraper = SummaryScraper(get_cached_session(),
                                     get_cached_session('question-pdf'))
    records = summary_scraper.fetch_summaries(year, get_pdf_text=True)

    patcher.update(records)


@scraper_manager.command
def proposals():
    from mptracker.scraper.proposals import ProposalScraper

    proposal_scraper = ProposalScraper(get_cached_session())

    records = proposal_scraper.fetch_proposals()

    proposal_patcher = TablePatcher(models.Proposal,
                                    models.db.session,
                                    key_columns=['cdep_serial'])

    person_matcher = models.PersonMatcher()

    with proposal_patcher.process(autoflush=1000) as add:
        for record in records:
            if record['sponsored_by'] == 'cdep':
                cdep_sponsors = record.pop('cdep_sponsors')
            else:
                cdep_sponsors = []
            result = add(record)
            row = result.row

            new_people = set()
            for sponsor_info in cdep_sponsors:
                person = person_matcher.get_person(sponsor_info['name'],
                                                   sponsor_info['cdep_id'],
                                                   strict=True)
                new_people.add(person)

            existing_people = set(row.sponsors)
            to_remove = set(existing_people) - set(new_people)
            to_add = set(new_people) - set(existing_people)
            if to_remove:
                logger.info("Removing sponsors: %r",
                            [p.cdep_id for p in to_remove])
            if to_add:
                logger.info("Adding sponsors: %r",
                            [p.cdep_id for p in to_add])

            row.sponsors = list(new_people)
