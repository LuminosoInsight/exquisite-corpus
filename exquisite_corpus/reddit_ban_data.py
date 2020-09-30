# I got a list of banned subreddits from
# https://www.reddit.com/r/ListOfSubreddits/wiki/banned
#
# I do not even want the _names_ of some of these places in the code, so here
# are their mmh3 hashes. See scripts/hasher.py for how this list was produced.
#
# Updated in June 2020, and now we use case-folded versions of the subreddit
# names in case their capitalization is inconsistent.

BANNED_SUBREDDITS = {
    -2122640182,
    -2115636363,
    -2115353832,
    -2111986387,
    -2100499385,
    -2100052381,
    -2093960605,
    -2093599310,
    -2067344054,
    -2050304543,
    -2036370519,
    -2020290428,
    -2014688289,
    -2012981687,
    -1984671947,
    -1975925898,
    -1973507072,
    -1940531519,
    -1939943916,
    -1929629635,
    -1929436490,
    -1926858992,
    -1926100429,
    -1922568309,
    -1912084345,
    -1888457204,
    -1852985825,
    -1841854800,
    -1836287520,
    -1796057838,
    -1769975635,
    -1765138810,
    -1758763955,
    -1738555404,
    -1737485847,
    -1730781039,
    -1726277015,
    -1711787551,
    -1707901878,
    -1702651954,
    -1680561221,
    -1650394911,
    -1646525672,
    -1641956401,
    -1627855773,
    -1604587921,
    -1599905889,
    -1595776450,
    -1589924738,
    -1587600434,
    -1587113939,
    -1582437171,
    -1581118361,
    -1562864067,
    -1556746382,
    -1550334664,
    -1534234697,
    -1529701659,
    -1525562974,
    -1523169648,
    -1515966158,
    -1515028315,
    -1482475151,
    -1481591615,
    -1477592110,
    -1465251906,
    -1461352767,
    -1461286756,
    -1456269589,
    -1443508896,
    -1414652915,
    -1404700312,
    -1402599499,
    -1399826257,
    -1361426961,
    -1357606959,
    -1343614015,
    -1342984244,
    -1337220419,
    -1335299475,
    -1323509692,
    -1316608483,
    -1284769401,
    -1279507530,
    -1260510483,
    -1247834771,
    -1232491288,
    -1227041830,
    -1219003523,
    -1203920988,
    -1187414322,
    -1182604220,
    -1177781501,
    -1168821965,
    -1168637501,
    -1166923942,
    -1155124167,
    -1148900786,
    -1148205172,
    -1143027065,
    -1137737913,
    -1110330017,
    -1095443768,
    -1085924034,
    -1080591632,
    -1074007682,
    -1051513223,
    -1037498753,
    -1015825200,
    -1011257271,
    -1009589854,
    -992774976,
    -989173653,
    -984701637,
    -973089762,
    -969840662,
    -968111032,
    -966346572,
    -937493884,
    -932443772,
    -932417815,
    -923372184,
    -918624657,
    -914024666,
    -867403606,
    -859087774,
    -832322665,
    -824730020,
    -819895152,
    -807361663,
    -750278376,
    -740075211,
    -734614626,
    -727522049,
    -701963329,
    -700093927,
    -699888280,
    -687583873,
    -686662559,
    -686562368,
    -674336947,
    -670884661,
    -660596550,
    -629078991,
    -628830243,
    -621671227,
    -620843861,
    -613855399,
    -603700189,
    -600959780,
    -584848898,
    -582940928,
    -578057467,
    -574426091,
    -563963217,
    -562584253,
    -546994156,
    -525680213,
    -490070370,
    -489511295,
    -489251267,
    -484186682,
    -429416525,
    -420448568,
    -416344967,
    -404710969,
    -403805439,
    -381199183,
    -380406867,
    -380207636,
    -373124970,
    -364942821,
    -349826933,
    -342088619,
    -336076826,
    -332920802,
    -330575510,
    -328372673,
    -324113278,
    -318075611,
    -312384940,
    -291465626,
    -277066462,
    -273212066,
    -264848853,
    -260630299,
    -237413691,
    -236888792,
    -234244613,
    -220373955,
    -215883075,
    -214245509,
    -207391760,
    -205819829,
    -163694918,
    -154965260,
    -145291206,
    -142332537,
    -138530155,
    -131625937,
    -118582188,
    -114021322,
    -113715497,
    -107665950,
    -95709818,
    -91878244,
    -90477014,
    -61890909,
    -59791398,
    -50403428,
    25037376,
    25362294,
    37610941,
    48824054,
    50861900,
    58501854,
    65251979,
    72466282,
    79058828,
    120383372,
    129608883,
    145688519,
    155546221,
    155760800,
    157183806,
    163063923,
    172658455,
    174305815,
    183433404,
    185247249,
    187030495,
    188748400,
    213710674,
    221109122,
    222547632,
    234157381,
    276581724,
    276607907,
    280375711,
    285654566,
    294616714,
    294957582,
    299189184,
    304341614,
    309673032,
    312351298,
    319765784,
    324833054,
    350906932,
    363651005,
    369277759,
    372875715,
    396569724,
    419963408,
    422208903,
    424241799,
    426117951,
    432462857,
    436782399,
    441617055,
    471750968,
    475377078,
    503866771,
    506047432,
    508723829,
    510548872,
    516667951,
    525607362,
    533606384,
    540741048,
    545324760,
    548556065,
    556791094,
    570177991,
    579187471,
    598807139,
    600776633,
    606230688,
    618789747,
    631827678,
    635387737,
    648469484,
    664230606,
    673426838,
    688803599,
    694507601,
    696570598,
    702338922,
    736315933,
    755562603,
    760759905,
    789060113,
    790678941,
    791831022,
    792295849,
    800577762,
    801084849,
    809981544,
    810662607,
    827816878,
    843064440,
    845150836,
    846625149,
    853865706,
    884291868,
    891913687,
    902335145,
    924694196,
    926110702,
    928197522,
    935737204,
    936652754,
    936946722,
    948077065,
    965984404,
    967538951,
    977756825,
    1005304168,
    1014236081,
    1023593243,
    1046560592,
    1047735862,
    1072262476,
    1078513251,
    1081560349,
    1084615235,
    1086198681,
    1095062243,
    1107001772,
    1112750417,
    1120912117,
    1135568833,
    1146436728,
    1154142289,
    1163723849,
    1166162709,
    1191113873,
    1202643662,
    1205786494,
    1212027532,
    1212413382,
    1215595997,
    1217830868,
    1218446855,
    1223862827,
    1230513165,
    1232658239,
    1239807137,
    1245930923,
    1292075875,
    1301845592,
    1344633868,
    1346489821,
    1348067736,
    1389641574,
    1390574285,
    1391788645,
    1403567762,
    1409010098,
    1420261781,
    1431400036,
    1431827897,
    1435061117,
    1444590460,
    1445643860,
    1471084999,
    1481391076,
    1482962327,
    1493242432,
    1498250624,
    1533388503,
    1533719996,
    1534288718,
    1545896522,
    1552279575,
    1561101898,
    1577832441,
    1582167871,
    1583625879,
    1587517792,
    1600463532,
    1601958693,
    1619303719,
    1676175756,
    1677102168,
    1680715369,
    1692544400,
    1696383636,
    1699584999,
    1728187434,
    1731950987,
    1734064388,
    1746439875,
    1746685302,
    1747405032,
    1790596529,
    1833523008,
    1836495973,
    1838259587,
    1857373389,
    1870852570,
    1877310213,
    1880383374,
    1883818958,
    1918081294,
    1922604644,
    1925027888,
    1927668448,
    1928375770,
    1938222836,
    1939568009,
    1939642950,
    1950682812,
    1951204073,
    1951229558,
    1957090390,
    1961602382,
    1977525698,
    1986818933,
    1992579358,
    2004744761,
    2010194080,
    2014795435,
    2019174610,
    2039112543,
    2056062740,
    2096285615,
    2102928996,
    2133220964,
    2134751240,
    2137686049,
    2147392036,
}
