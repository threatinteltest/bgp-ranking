# -*- coding: utf-8 -*-

from models import *
from cli import *


class client():
    """ client who permits to display information
        in the database
    """

    def list_ASNs(self):
        return ASNs.query.order_by(ASNs.asn).all()

    def list_ASNs_descriptions(self):
        return ASNs_descriptions.query.order_by(ASNs_descriptions.asn_asn).all()

    def list_IPs(self):
        return IPs.query.order_by(IPs.ip).all()

    def list_IPs_descriptions(self):
        return IPs_descriptions.query.order_by(IPs_descriptions.ip_ip).all()

    def ASN_descriptions(self,asn):
        return ASNs_descriptions.query.filter_by(\
asn=ASNs.query.filter_by(asn=asn).first()).all()
  
    def IP_of_ASN(self,asn):
        descs = ASN_descriptions(asn)
        ips = []
        for desc in descs:
            ips.append(IPs_descriptions.query.filter_by(asn=desc).all())
        return ips 

    def display_IPs_by_AS(self,asns):
        for asn in asns:
            print(asn)
            for ip in asn.ips:
                print(ip)


if __name__ == "__main__":
    #Just to check the url and print the result (ip addresses)
    cl = client()
    exit = False

    while exit == False:
        print "\n0 - Exit\n"
        print "1 - Display list_ASNs:\n"
        print "2 - Display list_ASNs_descriptions:\n"
        print "3 - Display list_IPs:\n"
        print "4 - Display list_IPs_descriptions:\n"
        choice = input("\nChoose an action: ")
        print "\nChoix:%s_" % choice

        if choice == 0:
            exit = True
        elif choice == 1:
            print cl.list_ASNs()
        elif choice == 2:
            print cl.list_ASNs_descriptions()
        elif choice == 3:
            print cl.list_IPs()
        elif choice == 4:
            print cl.list_IPs_descriptions()
        else:
            pass
    print "Exiting client.py ..."
