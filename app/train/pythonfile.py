import json

j='''{ "hosts":  {
             "example1.lab.com" : ["mysql", "apache"],
             "example2.lab.com" : ["sqlite", "nmap"],
             "example3.lab.com" : ["vim", "bind9"]
             }
}'''

specific_key='example2'

found=False
def pairs(args):
    for arg in args:
        if arg[0].startswith(specific_key):
            k,v=arg
            print (k,v)

json.loads(j,object_pairs_hook=pairs)