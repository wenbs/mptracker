""" Fetch and parse questions & interpellations """

import re
from datetime import datetime
from pyquery import PyQuery as pq
from mptracker.scraper.common import (Scraper, pqitems, get_cached_session,
                                      get_cdep_id)


class Question:

    def __str__(self):
        return ("<Question type={o.q_type}"
                         " number={o.number!r}"
                         " date={o.date_record}"
                         " person_name={o.person_name!r}"
                         " person_cdep_id={o.person_cdep_id}"
                         ">").format(o=self)


class QuestionScraper(Scraper):

    title_pattern = re.compile(r'^(?P<type>Întrebarea|Interpelarea) nr\.')
    types = {
        'Întrebarea': 'question',
        'Interpelarea': 'interpelation',
    }

    def normalize_space(self, text):
        return re.sub(r'\s+', ' ', text)

    def parse_date_dmy(self, text):
        return datetime.strptime(text, '%d-%m-%Y').date()

    def person_from_td(self, td):
        for link in pqitems(td, 'a'):
            href = link.attr('href')
            if href.startswith('http://www.cdep.ro/pls/'
                               'parlam/structura.mp?'):
                return link.text(), get_cdep_id(href)

    def get_question(self, href):
        page = self.fetch_url(href)
        heading = page('#pageHeader .pageHeaderLinks').text()
        heading_m = self.title_pattern.match(heading)
        assert heading_m is not None, "Could not parse heading %r" % heading
        question = Question()
        question.q_type = self.types[heading_m.group('type')]

        question.url = href

        rows = pqitems(page, '#pageContent > dd > table > tr')
        assert (self.normalize_space(next(rows).text()) ==
                'Informaţii privind interpelarea')

        for row in rows:
            norm_text = self.normalize_space(row.text())
            if norm_text == '':
                continue
            elif norm_text == 'Informaţii privind răspunsul':
                break

            [label, value] = [pq(el) for el in row[0]]
            label_text = label.text()

            if label_text == 'Nr.înregistrare:':
                question.number = value.text()
            elif label_text == 'Data înregistrarii:':
                question.date_record = self.parse_date_dmy(value.text())
            elif label_text == 'Mod adresare:':
                question.address_method = value.text()
            elif label_text == 'Destinatar:':
                question.target = value.text()
            elif label_text == 'Adresant:' or label_text == 'Adresanţi:':
                (question.person_name, question.person_cdep_id) = \
                    self.person_from_td(value)

        return question

    def run(self):
        index = self.fetch_url('http://www.cdep.ro/pls/parlam/'
                               'interpelari.lista?tip=&dat=2013&idl=1')
        for link in pqitems(index, '#pageContent table a'):
            href = link.attr('href')
            assert href.startswith('http://www.cdep.ro/pls/'
                                   'parlam/interpelari.detalii')

            yield self.get_question(href)


def main():
    import sys
    import csv
    steno_scraper = QuestionScraper(get_cached_session())
    out = csv.writer(sys.stdout)
    out.writerow(['person_name', 'person_cdep_id', 'number', 'date'])
    for question in steno_scraper.run():
        out.writerow([
            question.person_name,
            question.person_cdep_id,
            question.number,
            question.date_record,
        ])


if __name__ == '__main__':
    main()