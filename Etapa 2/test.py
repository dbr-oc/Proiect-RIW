#
# from datetime import datetime, timedelta
#
# now = datetime.now()
# print(now)
# b = now + timedelta(0, 30)
# print(b)
#
# c = b - now
# print(c.total_seconds())

import dns.resolver

result = dns.resolver.query('tutorialspoint.com', 'A')
for ipval in result:
    print('IP', ipval.to_text())