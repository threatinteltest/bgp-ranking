#!/usr/bin/python

"""
Quick and durty code generating reports based on the information found in the database. 

FIXME: rewrite it!
"""


if __name__ == "__main__":
    import os 
    import sys
    import ConfigParser
    config = ConfigParser.RawConfigParser()
    config.optionxform = str
    config.read("../../etc/bgp-ranking.conf")
    root_dir = config.get('directories','root')
    sys.path.append(os.path.join(root_dir,config.get('directories','libraries')))

from db_models.ranking import *


items = config.items('modules_to_parse')

from sqlalchemy import and_, desc

class Reports():
    
    def __init__(self, date = datetime.datetime.utcnow()):
        self.date = date
        self.impacts = {}
        for item in items:
            self.impacts[item[0]] = int(item[1])
    
    def get_sources(self):
        r_session = RankingSession()
        self.sources = []
        for s in Sources.query.all():
            self.sources.append(s.source)
        r_session.close()
    
    def filter_query_source(self, query, limit):
        entries = query.count()
        histories_by_asn = {}
        first = 0 
        last = limit
        while limit > 0:
            select = query[first:last]
            for s in select:
                if histories_by_asn.get(s.asn, None) is None:
                    if s.source_source is not None:
                        histories_by_asn[s.asn] = [s.timestamp, s.asn, s.rankv4 * float(self.impacts[str(s.source_source)]) + 1.0]
                    else:
                        histories_by_asn[s.asn] = [s.timestamp, s.asn, s.rankv4 + 1.0]
                    limit -= 1
                    if limit <= 0:
                        break
            first = last
            last = last + limit
            if first > entries:
                break
        return histories_by_asn

    #FIXME: query on IPv6
    def best_of_day(self, limit = 50, source = None):
        r_session = RankingSession()
        query = None
        histo = {}
        s = self.existing_source(source)
        if s is not None:
            query = History.query.filter(and_(History.source == s, and_(History.rankv4 > 0.0, and_(History.timestamp <= self.date, History.timestamp >= self.date - datetime.timedelta(days=1))))).order_by(desc(History.rankv4), desc(History.timestamp))
            histo = self.filter_query_source(query, limit)
            global_query = False
        if query is None:
            histo = {}
            for s in Sources.query.all():
                query = History.query.filter(and_(History.source == s, and_(History.rankv4 > 0.0, and_(History.timestamp <= self.date, History.timestamp >= self.date - datetime.timedelta(days=1))))).order_by(desc(History.rankv4), desc(History.timestamp))
                h_temp = self.filter_query_source(query, limit)
                if len(histo) == 0:
                    histo = h_temp
                else:
                    for t, h in h_temp.items():
                        if histo.get(h[1], None) is None:
                            histo[h[1]] = h
                        else:
                            histo[h[1]][2] += h[2] - 1 
        self.histories = []
        for t, h in histo.items():
            self.histories.append(h)
        self.histories.sort(key=lambda x:x[2], reverse=True )
        r_session.close()
    
    def asn_histo_query(self, asn, source = None):
        r_session = RankingSession()
        query = None
        s = self.existing_source(source)
        if s is not None:
            query = History.query.filter(and_(History.source == s, History.asn == int(asn))).order_by(desc(History.timestamp))
        if query is None: 
            query = History.query.filter(History.asn == int(asn)).order_by(desc(History.timestamp))
        r_session.close()
        return query

    def prepare_graphe_js(self,  asn, source = None):
        query = self.asn_histo_query(asn, source)
        histories = query.all()
        if histories is not None and len(histories) > 0:
            first_date = histories[-1].timestamp.date()
            last_date = histories[0].timestamp.date()
            date = None
            tmptable = []
            for history in histories:
                prec_date = date
                date = history.timestamp.date()
                if date != prec_date:
                    #FIXME: legacy code, to support the first version of the database: the source was not saved
                    if history.source_source is not None:
                        tmptable.append([str(history.timestamp.date()), float(history.rankv4) * float(self.impacts[str(history.source_source)]) + 1.0 , float(history.rankv6)* float(self.impacts[str(history.source_source)]) + 1.0] )
                    else:
                        tmptable.append([str(history.timestamp.date()), float(history.rankv4) + 1.0 , float(history.rankv6) + 1.0] )
            dates = []
            ipv4 = []
            ipv6 = []
            for t in reversed(tmptable):
                dates.append(t[0])
                ipv4.append(t[1])
                ipv6.append(t[2])
            self.graph_infos = [ipv4, ipv6, dates, first_date, last_date]
        else:
            self.graph_infos = None
    
    def existing_source(self, source = None):
        if source is not None and len(source) > 0:
            r_session = RankingSession()
            to_return = Sources.query.get(unicode(source))
            r_session.close()
            return to_return
        return None

    def ip_desc_query(self, asn_id, source, date):
        if source is not None and len(source) > 0:
            query = IPsDescriptions.query.filter(and_(IPsDescriptions.list_name == unicode(source), and_(IPsDescriptions.asn == asn_id, and_(IPsDescriptions.timestamp <= date, IPsDescriptions.timestamp >= date - datetime.timedelta(days=1)))))
        else: 
            query = IPsDescriptions.query.filter(and_(IPsDescriptions.asn == asn_id, and_(IPsDescriptions.timestamp <= date, IPsDescriptions.timestamp >= date - datetime.timedelta(days=1))))
        return query

    def get_asn_descs(self, asn, source = None):
        r_session = RankingSession()
        asn_db = ASNs.query.filter(ASNs.asn == int(asn)).first()
        if asn_db is not None:
            asn_descs = ASNsDescriptions.query.filter(ASNsDescriptions.asn == asn_db).all()
        else:
            asn_descs = None
        self.asn_descs_to_print = None
        self.graph_infos = None
        if asn_descs is not None and len(asn_descs) > 0:
            self.prepare_graphe_js(asn, source)
            self.asn_descs_to_print = []
            for desc in asn_descs:
                last_histo = self.asn_histo_query(asn, source).first()
                if last_histo is not None:
                    query = self.ip_desc_query(desc, source, last_histo.timestamp)
                    nb_of_ips = query.count()
                    if nb_of_ips > 0:
                        self.asn_descs_to_print.append([desc.id, desc.timestamp, desc.owner, desc.ips_block, nb_of_ips])
        r_session.close()

    def get_ips_descs(self, asn_desc_id, source = None):
        r_session = RankingSession()
        asn_desc = ASNsDescriptions.query.filter(ASNsDescriptions.id == int(asn_desc_id)).first()
        ip_descs = None
        if asn_desc is not None:
            last_histo = self.asn_histo_query(asn_desc.asn_asn,source).first()
            if last_histo is not None:
                query = self.ip_desc_query(asn_desc, source, last_histo.timestamp)
                ip_descs = query.all()
            r_session.close()
        else:
            ip_descs = None
        self.ip_descs_to_print = None
        if ip_descs is not None:
            self.ip_descs_to_print = []
            for desc in ip_descs:
                self.ip_descs_to_print.append([desc.timestamp, desc.ip_ip, desc.list_name, desc.infection, desc.raw_informations, desc.whois])
