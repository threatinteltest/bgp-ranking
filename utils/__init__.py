# -*- coding: utf-8 -*-
from models import *

import sys
reload(sys)
sys.setdefaultencoding('utf-8')

ranking_metadata.bind = ranking_engine
ranking_session.bind = ranking_engine

setup_all()
#ranking_metadata.drop_all()
ranking_metadata.create_all()

# Creation of the "default AS", see fetch_asn.py for more informations 
if not ASNs.query.get(unicode('-1')):
    ASNs(asn=unicode('-1'))
    ranking_session.commit()
