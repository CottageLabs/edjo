import re
from datetime import datetime

################ DISPLAY VALUE FUNCTIONS ###################

def value_map(dict, value):
    return dict.get(value, value)

def regex_map(dict, value):
    capture = re.findall(dict["expression"], value)
    if len(capture) == 1:
        return capture[0]
    return value
    
def wrap(dict, value):
    return dict['start'] + value + dict['end']
    
def doiify(dict, value):
    # dois may start with:
    # 10. - prefix http://dx.doi.org/
    # doi: - strip doi: and replace with http://dx.doi.org/
    # http://dx.doi.org/ already done, just linkify
    resolver = dict.get("resolver", "http://dx.doi.org/")
    link = None
    if value.startswith("10."):
        link = resolver + value
    elif value.startswith("doi:"):
        link = resolver + value[4:]
    elif value.startswith("http://"):
        link = value
    
    if link is not None:
        return '<a href="' + link + '">' + value + '</a>'
    else:
        return value

def linkify(dict, value):
    parts = _get_location_pairs(value, "http://", " ")
    
    # read into a sortable dictionary
    d = {}
    for (s, f) in parts:
        d[s] = f
    
    # sort the starting points
    keys = d.keys()
    keys.sort()
    
    # determine the splitting points
    split_at = [0]
    for s in keys:
        f = d.get(s)
        split_at.append(s)
        split_at.append(f)
    
    # turn the splitting points into pairs
    pairs = []
    for i in range(0, len(split_at)):
        if split_at[i] == -1:
            break
        if i + 1 >= len(split_at):
            end = len(nm)
        elif split_at[i+1] == -1:
            end = len(nm)
        else:
            end = split_at[i+1]
        pair = (split_at[i], end)
        pairs.append(pair)
    
    frags = []
    for s, f in pairs:
        frags.append(nm[s:f])
    
    for i in range(len(frags)):
        if frags[i].startswith("http://"):
            frags[i] = _create_url(frags[i])
    
    message = "".join(frags)
    return message

def _get_location_pairs(message, start_sub, finish_sub):
    idx = 0
    pairs = []
    while message.find(start_sub, idx) > -1:
        si = message.find(start_sub, idx)
        sf = message.find(finish_sub, si)
        pairs.append((si, sf))
        idx = sf
    return pairs

def _create_url(url):
    return "<a href=\"%(url)s\">%(url)s</a>" % {"url" : url}

################ UPPER DISPLAY FUNCTIONS ####################

def years_different(dict, lower, upper):
    lyear = regex_map({"expression" : "([\\d]{4})-.*"}, unicode(lower))
    uyear = regex_map({"expression" : "([\\d]{4})-.*"}, unicode(upper))
    return lyear != uyear

################ GENERATOR FUNCTIONS ########################

def date_range_count(dict, args, result, value=None):
    # this function does not support chained values
    if not args['q'].has_key(dict['bounding_field']):
        values = result.get(dict['results_field'])
        if values is not None:
            return str(len(values))
        else:
            return 0
    start, end = args['q'][dict['bounding_field']]
    sdate = datetime.strptime(start, "%Y-%m-%dT%H:%M:%SZ")
    edate = datetime.strptime(end, "%Y-%m-%dT%H:%M:%SZ")
    values = result.get(dict['results_field'])
    if values is None:
        return 0
    count = 0
    for vdate in values:
        # convert to offset aware datetime
        strdate = '{0.year}-{0.month:{1}}-{0.day:{1}}T{0.hour:{1}}:{0.minute:{1}}:{0.second:{1}}Z'.format(vdate, '02')
        vdate = datetime.strptime(strdate, "%Y-%m-%dT%H:%M:%SZ")
        if vdate >= sdate and vdate <= edate:
            count += 1
    return str(count)
    
def array_count(dict, args, result, value=None):
    # this function does not support chained values
    values = result.get(dict['count_field'])
    if values is None:
        return 0
    return len(values)
    