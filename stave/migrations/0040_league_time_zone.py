# Generated by Django 5.1.4 on 2025-04-26 04:44

from zoneinfo import ZoneInfo

from django.db import migrations, models


def update_timezones(apps, schema_editor):
    Game = apps.get_model("stave", "Game")
    for game in Game.objects.all():
        if game.start_time:
            game.start_time = game.start_time.replace(
                tzinfo=ZoneInfo(game.event.league.time_zone)
            )
        if game.end_time:
            game.end_time = game.end_time.replace(
                tzinfo=ZoneInfo(game.event.league.time_zone)
            )

        game.save()


class Migration(migrations.Migration):
    dependencies = [
        ("stave", "0039_rename_decline_email_sent_application_rejection_email_sent"),
    ]

    operations = [
        migrations.AddField(
            model_name="league",
            name="time_zone",
            field=models.CharField(
                choices=[
                    ("America/Cuiaba", "America/Cuiaba"),
                    ("Europe/Zurich", "Europe/Zurich"),
                    ("America/Sao_Paulo", "America/Sao_Paulo"),
                    ("Africa/Brazzaville", "Africa/Brazzaville"),
                    ("Europe/Dublin", "Europe/Dublin"),
                    ("America/St_Thomas", "America/St_Thomas"),
                    ("America/Pangnirtung", "America/Pangnirtung"),
                    ("Asia/Krasnoyarsk", "Asia/Krasnoyarsk"),
                    ("Asia/Nicosia", "Asia/Nicosia"),
                    ("Africa/Dar_es_Salaam", "Africa/Dar_es_Salaam"),
                    ("America/Argentina/Catamarca", "America/Argentina/Catamarca"),
                    ("Pacific/Bougainville", "Pacific/Bougainville"),
                    ("Etc/Zulu", "Etc/Zulu"),
                    ("America/Goose_Bay", "America/Goose_Bay"),
                    ("Indian/Cocos", "Indian/Cocos"),
                    ("Pacific/Wallis", "Pacific/Wallis"),
                    ("America/Fortaleza", "America/Fortaleza"),
                    ("America/Eirunepe", "America/Eirunepe"),
                    ("Africa/Bamako", "Africa/Bamako"),
                    ("Atlantic/Stanley", "Atlantic/Stanley"),
                    (
                        "America/Argentina/Rio_Gallegos",
                        "America/Argentina/Rio_Gallegos",
                    ),
                    ("America/Glace_Bay", "America/Glace_Bay"),
                    ("Etc/GMT-12", "Etc/GMT-12"),
                    ("Australia/ACT", "Australia/ACT"),
                    ("US/Pacific", "US/Pacific"),
                    ("Australia/Brisbane", "Australia/Brisbane"),
                    ("Europe/Warsaw", "Europe/Warsaw"),
                    ("Asia/Kathmandu", "Asia/Kathmandu"),
                    ("Asia/Thimphu", "Asia/Thimphu"),
                    ("Africa/Bujumbura", "Africa/Bujumbura"),
                    ("America/Manaus", "America/Manaus"),
                    ("Africa/Sao_Tome", "Africa/Sao_Tome"),
                    ("Pacific/Kanton", "Pacific/Kanton"),
                    ("America/Knox_IN", "America/Knox_IN"),
                    ("Africa/Porto-Novo", "Africa/Porto-Novo"),
                    ("Asia/Qatar", "Asia/Qatar"),
                    ("America/Virgin", "America/Virgin"),
                    ("Africa/Casablanca", "Africa/Casablanca"),
                    ("America/Argentina/Tucuman", "America/Argentina/Tucuman"),
                    ("Pacific/Apia", "Pacific/Apia"),
                    ("Europe/Ulyanovsk", "Europe/Ulyanovsk"),
                    ("America/Catamarca", "America/Catamarca"),
                    ("America/Marigot", "America/Marigot"),
                    ("US/Alaska", "US/Alaska"),
                    ("W-SU", "W-SU"),
                    ("America/Argentina/Salta", "America/Argentina/Salta"),
                    ("Pacific/Midway", "Pacific/Midway"),
                    ("America/Rosario", "America/Rosario"),
                    ("US/Aleutian", "US/Aleutian"),
                    ("Asia/Kuching", "Asia/Kuching"),
                    ("America/Miquelon", "America/Miquelon"),
                    ("Europe/Tallinn", "Europe/Tallinn"),
                    ("Pacific/Galapagos", "Pacific/Galapagos"),
                    ("Asia/Katmandu", "Asia/Katmandu"),
                    ("Europe/Malta", "Europe/Malta"),
                    ("Africa/Accra", "Africa/Accra"),
                    ("Europe/Stockholm", "Europe/Stockholm"),
                    ("Pacific/Majuro", "Pacific/Majuro"),
                    ("America/Phoenix", "America/Phoenix"),
                    ("Etc/Greenwich", "Etc/Greenwich"),
                    ("Europe/Zagreb", "Europe/Zagreb"),
                    ("Australia/NSW", "Australia/NSW"),
                    ("Asia/Oral", "Asia/Oral"),
                    ("Asia/Gaza", "Asia/Gaza"),
                    ("Europe/Mariehamn", "Europe/Mariehamn"),
                    ("America/Thunder_Bay", "America/Thunder_Bay"),
                    ("Antarctica/Rothera", "Antarctica/Rothera"),
                    ("Asia/Pontianak", "Asia/Pontianak"),
                    ("Europe/Vatican", "Europe/Vatican"),
                    ("Africa/Maputo", "Africa/Maputo"),
                    ("Antarctica/McMurdo", "Antarctica/McMurdo"),
                    ("Indian/Maldives", "Indian/Maldives"),
                    ("Europe/Andorra", "Europe/Andorra"),
                    ("Africa/Mogadishu", "Africa/Mogadishu"),
                    ("Europe/Simferopol", "Europe/Simferopol"),
                    ("America/Metlakatla", "America/Metlakatla"),
                    ("America/Scoresbysund", "America/Scoresbysund"),
                    ("Singapore", "Singapore"),
                    ("Asia/Aqtobe", "Asia/Aqtobe"),
                    ("Australia/Victoria", "Australia/Victoria"),
                    ("GMT0", "GMT0"),
                    ("Asia/Brunei", "Asia/Brunei"),
                    ("Africa/Kigali", "Africa/Kigali"),
                    ("America/St_Kitts", "America/St_Kitts"),
                    ("Europe/Oslo", "Europe/Oslo"),
                    ("Asia/Beirut", "Asia/Beirut"),
                    ("America/Porto_Velho", "America/Porto_Velho"),
                    ("Africa/Lusaka", "Africa/Lusaka"),
                    ("America/Argentina/Jujuy", "America/Argentina/Jujuy"),
                    ("Etc/GMT+1", "Etc/GMT+1"),
                    ("America/Coral_Harbour", "America/Coral_Harbour"),
                    ("America/Managua", "America/Managua"),
                    ("Europe/Zaporozhye", "Europe/Zaporozhye"),
                    ("Pacific/Guadalcanal", "Pacific/Guadalcanal"),
                    ("America/Swift_Current", "America/Swift_Current"),
                    ("Africa/Timbuktu", "Africa/Timbuktu"),
                    ("Arctic/Longyearbyen", "Arctic/Longyearbyen"),
                    ("Asia/Yangon", "Asia/Yangon"),
                    ("America/Santiago", "America/Santiago"),
                    ("Asia/Aqtau", "Asia/Aqtau"),
                    ("America/Detroit", "America/Detroit"),
                    ("America/Curacao", "America/Curacao"),
                    ("America/Tortola", "America/Tortola"),
                    ("Asia/Khandyga", "Asia/Khandyga"),
                    ("America/Juneau", "America/Juneau"),
                    ("Africa/Tunis", "Africa/Tunis"),
                    ("America/Whitehorse", "America/Whitehorse"),
                    ("Africa/Niamey", "Africa/Niamey"),
                    ("Pacific/Guam", "Pacific/Guam"),
                    ("America/Mexico_City", "America/Mexico_City"),
                    ("Europe/Luxembourg", "Europe/Luxembourg"),
                    ("America/Bahia_Banderas", "America/Bahia_Banderas"),
                    ("Asia/Seoul", "Asia/Seoul"),
                    ("Etc/GMT-5", "Etc/GMT-5"),
                    ("Pacific/Fiji", "Pacific/Fiji"),
                    ("Europe/Belgrade", "Europe/Belgrade"),
                    ("Atlantic/Faroe", "Atlantic/Faroe"),
                    ("America/Boa_Vista", "America/Boa_Vista"),
                    ("America/Argentina/Mendoza", "America/Argentina/Mendoza"),
                    ("Etc/GMT-6", "Etc/GMT-6"),
                    ("America/Lower_Princes", "America/Lower_Princes"),
                    ("Australia/Broken_Hill", "Australia/Broken_Hill"),
                    ("America/Tegucigalpa", "America/Tegucigalpa"),
                    ("US/Arizona", "US/Arizona"),
                    ("Indian/Chagos", "Indian/Chagos"),
                    ("Asia/Ashgabat", "Asia/Ashgabat"),
                    ("US/Hawaii", "US/Hawaii"),
                    ("America/Campo_Grande", "America/Campo_Grande"),
                    ("America/Fort_Nelson", "America/Fort_Nelson"),
                    ("Atlantic/St_Helena", "Atlantic/St_Helena"),
                    ("Asia/Kabul", "Asia/Kabul"),
                    ("America/Moncton", "America/Moncton"),
                    ("Asia/Anadyr", "Asia/Anadyr"),
                    ("Etc/GMT-9", "Etc/GMT-9"),
                    ("Etc/Universal", "Etc/Universal"),
                    ("Etc/GMT+9", "Etc/GMT+9"),
                    ("Atlantic/Reykjavik", "Atlantic/Reykjavik"),
                    ("America/Anchorage", "America/Anchorage"),
                    ("America/Nuuk", "America/Nuuk"),
                    ("Canada/Eastern", "Canada/Eastern"),
                    ("Asia/Tehran", "Asia/Tehran"),
                    ("Indian/Mauritius", "Indian/Mauritius"),
                    ("US/Mountain", "US/Mountain"),
                    ("America/Indiana/Petersburg", "America/Indiana/Petersburg"),
                    ("Europe/Amsterdam", "Europe/Amsterdam"),
                    ("Europe/Bratislava", "Europe/Bratislava"),
                    ("Antarctica/South_Pole", "Antarctica/South_Pole"),
                    ("America/Cayman", "America/Cayman"),
                    ("Asia/Muscat", "Asia/Muscat"),
                    ("Africa/Monrovia", "Africa/Monrovia"),
                    ("Europe/Volgograd", "Europe/Volgograd"),
                    ("America/Adak", "America/Adak"),
                    ("MST", "MST"),
                    ("Canada/Mountain", "Canada/Mountain"),
                    ("Asia/Novosibirsk", "Asia/Novosibirsk"),
                    ("America/Atka", "America/Atka"),
                    ("Asia/Dhaka", "Asia/Dhaka"),
                    ("Pacific/Yap", "Pacific/Yap"),
                    ("Pacific/Niue", "Pacific/Niue"),
                    ("Europe/Kyiv", "Europe/Kyiv"),
                    ("Pacific/Easter", "Pacific/Easter"),
                    ("America/Argentina/San_Luis", "America/Argentina/San_Luis"),
                    ("UCT", "UCT"),
                    ("Europe/Berlin", "Europe/Berlin"),
                    ("America/Buenos_Aires", "America/Buenos_Aires"),
                    ("Australia/Perth", "Australia/Perth"),
                    ("America/Santo_Domingo", "America/Santo_Domingo"),
                    ("Etc/GMT+8", "Etc/GMT+8"),
                    ("Asia/Karachi", "Asia/Karachi"),
                    ("US/Eastern", "US/Eastern"),
                    ("Antarctica/DumontDUrville", "Antarctica/DumontDUrville"),
                    ("Asia/Rangoon", "Asia/Rangoon"),
                    ("Mexico/BajaNorte", "Mexico/BajaNorte"),
                    ("Zulu", "Zulu"),
                    ("America/Argentina/Cordoba", "America/Argentina/Cordoba"),
                    ("Europe/Sarajevo", "Europe/Sarajevo"),
                    ("America/Bogota", "America/Bogota"),
                    ("Canada/Saskatchewan", "Canada/Saskatchewan"),
                    ("America/Guyana", "America/Guyana"),
                    ("Asia/Dubai", "Asia/Dubai"),
                    ("Pacific/Nauru", "Pacific/Nauru"),
                    ("Asia/Yekaterinburg", "Asia/Yekaterinburg"),
                    ("Pacific/Kwajalein", "Pacific/Kwajalein"),
                    ("Africa/Ouagadougou", "Africa/Ouagadougou"),
                    ("America/Merida", "America/Merida"),
                    ("Etc/GMT+6", "Etc/GMT+6"),
                    ("Brazil/DeNoronha", "Brazil/DeNoronha"),
                    ("Asia/Shanghai", "Asia/Shanghai"),
                    ("Europe/Bucharest", "Europe/Bucharest"),
                    ("America/Yellowknife", "America/Yellowknife"),
                    ("Asia/Dacca", "Asia/Dacca"),
                    ("US/Central", "US/Central"),
                    ("Eire", "Eire"),
                    ("Etc/GMT0", "Etc/GMT0"),
                    ("Asia/Riyadh", "Asia/Riyadh"),
                    ("US/East-Indiana", "US/East-Indiana"),
                    ("CST6CDT", "CST6CDT"),
                    ("Europe/Ljubljana", "Europe/Ljubljana"),
                    ("Africa/Lome", "Africa/Lome"),
                    ("Australia/Canberra", "Australia/Canberra"),
                    ("Etc/GMT+7", "Etc/GMT+7"),
                    ("Africa/Libreville", "Africa/Libreville"),
                    ("Asia/Macao", "Asia/Macao"),
                    ("America/Araguaina", "America/Araguaina"),
                    ("Europe/Riga", "Europe/Riga"),
                    ("Kwajalein", "Kwajalein"),
                    ("Europe/Prague", "Europe/Prague"),
                    ("Etc/GMT-1", "Etc/GMT-1"),
                    ("Etc/GMT-10", "Etc/GMT-10"),
                    ("Asia/Bangkok", "Asia/Bangkok"),
                    ("Europe/Jersey", "Europe/Jersey"),
                    ("America/Indianapolis", "America/Indianapolis"),
                    ("Asia/Kolkata", "Asia/Kolkata"),
                    ("Asia/Jakarta", "Asia/Jakarta"),
                    ("Africa/Harare", "Africa/Harare"),
                    ("Europe/Samara", "Europe/Samara"),
                    ("Asia/Phnom_Penh", "Asia/Phnom_Penh"),
                    ("America/Indiana/Vevay", "America/Indiana/Vevay"),
                    ("Australia/North", "Australia/North"),
                    ("Africa/Khartoum", "Africa/Khartoum"),
                    ("Asia/Ashkhabad", "Asia/Ashkhabad"),
                    ("Canada/Atlantic", "Canada/Atlantic"),
                    ("Israel", "Israel"),
                    ("Africa/Bangui", "Africa/Bangui"),
                    ("America/Guayaquil", "America/Guayaquil"),
                    ("America/Maceio", "America/Maceio"),
                    ("Europe/Gibraltar", "Europe/Gibraltar"),
                    ("Asia/Urumqi", "Asia/Urumqi"),
                    ("Pacific/Honolulu", "Pacific/Honolulu"),
                    ("America/Guatemala", "America/Guatemala"),
                    ("Indian/Antananarivo", "Indian/Antananarivo"),
                    ("America/Havana", "America/Havana"),
                    ("Africa/Ceuta", "Africa/Ceuta"),
                    ("Antarctica/Syowa", "Antarctica/Syowa"),
                    ("Africa/Freetown", "Africa/Freetown"),
                    ("America/Asuncion", "America/Asuncion"),
                    ("Asia/Samarkand", "Asia/Samarkand"),
                    ("Canada/Central", "Canada/Central"),
                    ("Antarctica/Vostok", "Antarctica/Vostok"),
                    ("Atlantic/Cape_Verde", "Atlantic/Cape_Verde"),
                    ("Antarctica/Mawson", "Antarctica/Mawson"),
                    ("Cuba", "Cuba"),
                    ("Libya", "Libya"),
                    ("Greenwich", "Greenwich"),
                    ("Australia/Lord_Howe", "Australia/Lord_Howe"),
                    ("MET", "MET"),
                    ("America/Danmarkshavn", "America/Danmarkshavn"),
                    ("Pacific/Tongatapu", "Pacific/Tongatapu"),
                    ("Africa/Abidjan", "Africa/Abidjan"),
                    ("Asia/Manila", "Asia/Manila"),
                    ("Etc/GMT-14", "Etc/GMT-14"),
                    ("Australia/Melbourne", "Australia/Melbourne"),
                    ("America/Toronto", "America/Toronto"),
                    ("Pacific/Fakaofo", "Pacific/Fakaofo"),
                    ("Asia/Tokyo", "Asia/Tokyo"),
                    ("America/Nome", "America/Nome"),
                    ("Etc/GMT+0", "Etc/GMT+0"),
                    ("Asia/Chongqing", "Asia/Chongqing"),
                    ("America/Inuvik", "America/Inuvik"),
                    ("Pacific/Kosrae", "Pacific/Kosrae"),
                    ("Asia/Singapore", "Asia/Singapore"),
                    ("Etc/GMT+5", "Etc/GMT+5"),
                    ("Europe/Copenhagen", "Europe/Copenhagen"),
                    ("Portugal", "Portugal"),
                    ("Indian/Reunion", "Indian/Reunion"),
                    ("Asia/Sakhalin", "Asia/Sakhalin"),
                    ("America/Hermosillo", "America/Hermosillo"),
                    ("Pacific/Marquesas", "Pacific/Marquesas"),
                    ("America/Barbados", "America/Barbados"),
                    ("Asia/Srednekolymsk", "Asia/Srednekolymsk"),
                    ("America/St_Vincent", "America/St_Vincent"),
                    ("America/Matamoros", "America/Matamoros"),
                    ("Asia/Bishkek", "Asia/Bishkek"),
                    ("Etc/GMT-4", "Etc/GMT-4"),
                    ("Etc/GMT-0", "Etc/GMT-0"),
                    ("Turkey", "Turkey"),
                    ("Europe/Uzhgorod", "Europe/Uzhgorod"),
                    ("US/Indiana-Starke", "US/Indiana-Starke"),
                    ("Asia/Aden", "Asia/Aden"),
                    ("Etc/GMT-8", "Etc/GMT-8"),
                    ("GMT+0", "GMT+0"),
                    ("America/Aruba", "America/Aruba"),
                    ("Asia/Makassar", "Asia/Makassar"),
                    ("Australia/South", "Australia/South"),
                    (
                        "America/Argentina/Buenos_Aires",
                        "America/Argentina/Buenos_Aires",
                    ),
                    ("Europe/Istanbul", "Europe/Istanbul"),
                    ("Europe/Nicosia", "Europe/Nicosia"),
                    ("Atlantic/Bermuda", "Atlantic/Bermuda"),
                    ("Asia/Kamchatka", "Asia/Kamchatka"),
                    ("Asia/Damascus", "Asia/Damascus"),
                    ("Europe/Tirane", "Europe/Tirane"),
                    ("Australia/Eucla", "Australia/Eucla"),
                    (
                        "America/Argentina/ComodRivadavia",
                        "America/Argentina/ComodRivadavia",
                    ),
                    ("Africa/Maseru", "Africa/Maseru"),
                    ("US/Michigan", "US/Michigan"),
                    ("HST", "HST"),
                    ("Asia/Qyzylorda", "Asia/Qyzylorda"),
                    ("Africa/Bissau", "Africa/Bissau"),
                    ("America/Winnipeg", "America/Winnipeg"),
                    ("America/Indiana/Marengo", "America/Indiana/Marengo"),
                    ("America/Indiana/Tell_City", "America/Indiana/Tell_City"),
                    ("Pacific/Samoa", "Pacific/Samoa"),
                    ("Chile/EasterIsland", "Chile/EasterIsland"),
                    ("Etc/GMT-13", "Etc/GMT-13"),
                    ("Pacific/Port_Moresby", "Pacific/Port_Moresby"),
                    ("Indian/Comoro", "Indian/Comoro"),
                    ("Asia/Chungking", "Asia/Chungking"),
                    ("Pacific/Chatham", "Pacific/Chatham"),
                    ("Australia/LHI", "Australia/LHI"),
                    ("America/Indiana/Vincennes", "America/Indiana/Vincennes"),
                    ("Etc/GMT-11", "Etc/GMT-11"),
                    ("Antarctica/Casey", "Antarctica/Casey"),
                    ("America/Panama", "America/Panama"),
                    ("America/Santarem", "America/Santarem"),
                    ("Pacific/Tahiti", "Pacific/Tahiti"),
                    ("Africa/Blantyre", "Africa/Blantyre"),
                    ("Africa/Windhoek", "Africa/Windhoek"),
                    ("Atlantic/South_Georgia", "Atlantic/South_Georgia"),
                    ("Pacific/Pago_Pago", "Pacific/Pago_Pago"),
                    ("Factory", "Factory"),
                    ("Africa/Algiers", "Africa/Algiers"),
                    ("Africa/Johannesburg", "Africa/Johannesburg"),
                    ("America/Cambridge_Bay", "America/Cambridge_Bay"),
                    ("America/Dawson_Creek", "America/Dawson_Creek"),
                    ("Pacific/Johnston", "Pacific/Johnston"),
                    ("America/Iqaluit", "America/Iqaluit"),
                    ("America/El_Salvador", "America/El_Salvador"),
                    ("America/Recife", "America/Recife"),
                    ("Africa/Dakar", "Africa/Dakar"),
                    ("America/Los_Angeles", "America/Los_Angeles"),
                    ("America/North_Dakota/Beulah", "America/North_Dakota/Beulah"),
                    ("Mexico/General", "Mexico/General"),
                    ("America/Halifax", "America/Halifax"),
                    ("Asia/Istanbul", "Asia/Istanbul"),
                    ("Etc/UCT", "Etc/UCT"),
                    ("America/Montevideo", "America/Montevideo"),
                    ("Africa/Tripoli", "Africa/Tripoli"),
                    ("Canada/Yukon", "Canada/Yukon"),
                    ("America/Argentina/La_Rioja", "America/Argentina/La_Rioja"),
                    ("Pacific/Kiritimati", "Pacific/Kiritimati"),
                    ("Pacific/Gambier", "Pacific/Gambier"),
                    ("Europe/Chisinau", "Europe/Chisinau"),
                    ("Asia/Omsk", "Asia/Omsk"),
                    ("Asia/Ho_Chi_Minh", "Asia/Ho_Chi_Minh"),
                    ("Atlantic/Jan_Mayen", "Atlantic/Jan_Mayen"),
                    ("America/Punta_Arenas", "America/Punta_Arenas"),
                    ("Europe/Minsk", "Europe/Minsk"),
                    ("Atlantic/Madeira", "Atlantic/Madeira"),
                    ("Australia/Lindeman", "Australia/Lindeman"),
                    ("NZ", "NZ"),
                    ("Africa/Lubumbashi", "Africa/Lubumbashi"),
                    ("America/Grenada", "America/Grenada"),
                    ("America/New_York", "America/New_York"),
                    ("Europe/Kirov", "Europe/Kirov"),
                    ("America/Port-au-Prince", "America/Port-au-Prince"),
                    ("Iran", "Iran"),
                    ("America/Monterrey", "America/Monterrey"),
                    ("Canada/Pacific", "Canada/Pacific"),
                    ("Europe/Rome", "Europe/Rome"),
                    ("America/Rainy_River", "America/Rainy_River"),
                    ("Africa/Douala", "Africa/Douala"),
                    ("Europe/Astrakhan", "Europe/Astrakhan"),
                    ("Pacific/Pohnpei", "Pacific/Pohnpei"),
                    ("America/Grand_Turk", "America/Grand_Turk"),
                    ("GMT", "GMT"),
                    ("America/Shiprock", "America/Shiprock"),
                    ("America/Indiana/Knox", "America/Indiana/Knox"),
                    ("America/Jujuy", "America/Jujuy"),
                    ("Etc/GMT-2", "Etc/GMT-2"),
                    ("Etc/GMT", "Etc/GMT"),
                    ("Africa/Cairo", "Africa/Cairo"),
                    ("CET", "CET"),
                    ("Africa/Banjul", "Africa/Banjul"),
                    ("GMT-0", "GMT-0"),
                    ("America/St_Lucia", "America/St_Lucia"),
                    ("Asia/Vientiane", "Asia/Vientiane"),
                    ("America/Jamaica", "America/Jamaica"),
                    ("Asia/Choibalsan", "Asia/Choibalsan"),
                    ("Australia/Darwin", "Australia/Darwin"),
                    ("Asia/Ujung_Pandang", "Asia/Ujung_Pandang"),
                    ("America/Caracas", "America/Caracas"),
                    ("Pacific/Pitcairn", "Pacific/Pitcairn"),
                    ("Asia/Macau", "Asia/Macau"),
                    ("Asia/Hovd", "Asia/Hovd"),
                    ("Antarctica/Davis", "Antarctica/Davis"),
                    ("America/Louisville", "America/Louisville"),
                    ("EST", "EST"),
                    ("Africa/Asmera", "Africa/Asmera"),
                    ("Atlantic/Faeroe", "Atlantic/Faeroe"),
                    ("Asia/Baghdad", "Asia/Baghdad"),
                    ("Asia/Jerusalem", "Asia/Jerusalem"),
                    ("America/Porto_Acre", "America/Porto_Acre"),
                    ("Antarctica/Palmer", "Antarctica/Palmer"),
                    ("Europe/Sofia", "Europe/Sofia"),
                    ("Europe/Podgorica", "Europe/Podgorica"),
                    ("America/Tijuana", "America/Tijuana"),
                    ("Asia/Hebron", "Asia/Hebron"),
                    ("Antarctica/Troll", "Antarctica/Troll"),
                    ("America/Ojinaga", "America/Ojinaga"),
                    ("Pacific/Rarotonga", "Pacific/Rarotonga"),
                    ("Pacific/Funafuti", "Pacific/Funafuti"),
                    ("Etc/GMT+12", "Etc/GMT+12"),
                    ("America/Chicago", "America/Chicago"),
                    ("Pacific/Enderbury", "Pacific/Enderbury"),
                    ("Europe/Kaliningrad", "Europe/Kaliningrad"),
                    ("Europe/Kiev", "Europe/Kiev"),
                    ("Antarctica/Macquarie", "Antarctica/Macquarie"),
                    ("Australia/Adelaide", "Australia/Adelaide"),
                    ("Canada/Newfoundland", "Canada/Newfoundland"),
                    ("Asia/Kashgar", "Asia/Kashgar"),
                    ("Atlantic/Canary", "Atlantic/Canary"),
                    ("America/Ensenada", "America/Ensenada"),
                    ("Brazil/West", "Brazil/West"),
                    ("Egypt", "Egypt"),
                    ("Asia/Tel_Aviv", "Asia/Tel_Aviv"),
                    ("Europe/Paris", "Europe/Paris"),
                    ("Europe/Madrid", "Europe/Madrid"),
                    ("Indian/Kerguelen", "Indian/Kerguelen"),
                    ("Africa/Kampala", "Africa/Kampala"),
                    ("America/Resolute", "America/Resolute"),
                    ("Indian/Christmas", "Indian/Christmas"),
                    ("NZ-CHAT", "NZ-CHAT"),
                    ("Europe/Lisbon", "Europe/Lisbon"),
                    ("Africa/Asmara", "Africa/Asmara"),
                    ("Europe/Tiraspol", "Europe/Tiraspol"),
                    ("Asia/Yerevan", "Asia/Yerevan"),
                    ("Europe/Busingen", "Europe/Busingen"),
                    ("Australia/Tasmania", "Australia/Tasmania"),
                    ("Africa/Juba", "Africa/Juba"),
                    ("Asia/Chita", "Asia/Chita"),
                    ("Asia/Calcutta", "Asia/Calcutta"),
                    ("America/Bahia", "America/Bahia"),
                    ("Europe/Vienna", "Europe/Vienna"),
                    ("Brazil/Acre", "Brazil/Acre"),
                    ("Europe/Monaco", "Europe/Monaco"),
                    ("Pacific/Saipan", "Pacific/Saipan"),
                    ("Asia/Bahrain", "Asia/Bahrain"),
                    ("Asia/Dushanbe", "Asia/Dushanbe"),
                    ("America/Kentucky/Louisville", "America/Kentucky/Louisville"),
                    ("Asia/Famagusta", "Asia/Famagusta"),
                    ("Europe/Skopje", "Europe/Skopje"),
                    ("Asia/Hong_Kong", "Asia/Hong_Kong"),
                    ("America/Creston", "America/Creston"),
                    ("Etc/UTC", "Etc/UTC"),
                    ("America/Godthab", "America/Godthab"),
                    ("WET", "WET"),
                    ("Asia/Vladivostok", "Asia/Vladivostok"),
                    ("Etc/GMT-7", "Etc/GMT-7"),
                    ("Australia/Hobart", "Australia/Hobart"),
                    ("Europe/Athens", "Europe/Athens"),
                    ("America/Nipigon", "America/Nipigon"),
                    ("Pacific/Chuuk", "Pacific/Chuuk"),
                    ("Etc/GMT+4", "Etc/GMT+4"),
                    ("America/Montserrat", "America/Montserrat"),
                    ("Europe/Budapest", "Europe/Budapest"),
                    ("Asia/Qostanay", "Asia/Qostanay"),
                    ("America/Cayenne", "America/Cayenne"),
                    ("America/Menominee", "America/Menominee"),
                    ("Asia/Barnaul", "Asia/Barnaul"),
                    ("America/Cancun", "America/Cancun"),
                    ("Europe/Vaduz", "Europe/Vaduz"),
                    ("America/Antigua", "America/Antigua"),
                    ("America/Boise", "America/Boise"),
                    ("America/Martinique", "America/Martinique"),
                    ("America/Atikokan", "America/Atikokan"),
                    ("America/Kentucky/Monticello", "America/Kentucky/Monticello"),
                    ("America/Costa_Rica", "America/Costa_Rica"),
                    ("America/Regina", "America/Regina"),
                    ("Africa/Malabo", "Africa/Malabo"),
                    ("Europe/Helsinki", "Europe/Helsinki"),
                    ("Asia/Harbin", "Asia/Harbin"),
                    ("America/Guadeloupe", "America/Guadeloupe"),
                    ("America/Argentina/Ushuaia", "America/Argentina/Ushuaia"),
                    ("America/Indiana/Indianapolis", "America/Indiana/Indianapolis"),
                    ("Africa/Lagos", "Africa/Lagos"),
                    ("America/Belem", "America/Belem"),
                    ("America/Cordoba", "America/Cordoba"),
                    ("Africa/Nouakchott", "Africa/Nouakchott"),
                    ("Asia/Ust-Nera", "Asia/Ust-Nera"),
                    ("Etc/GMT+2", "Etc/GMT+2"),
                    ("Asia/Magadan", "Asia/Magadan"),
                    ("Asia/Novokuznetsk", "Asia/Novokuznetsk"),
                    ("Pacific/Efate", "Pacific/Efate"),
                    ("Pacific/Noumea", "Pacific/Noumea"),
                    ("Europe/Saratov", "Europe/Saratov"),
                    ("America/Thule", "America/Thule"),
                    ("Europe/Moscow", "Europe/Moscow"),
                    ("Asia/Dili", "Asia/Dili"),
                    ("Indian/Mahe", "Indian/Mahe"),
                    ("America/Vancouver", "America/Vancouver"),
                    ("Chile/Continental", "Chile/Continental"),
                    ("Asia/Kuwait", "Asia/Kuwait"),
                    (
                        "America/North_Dakota/New_Salem",
                        "America/North_Dakota/New_Salem",
                    ),
                    ("Poland", "Poland"),
                    ("Asia/Ulaanbaatar", "Asia/Ulaanbaatar"),
                    ("Asia/Baku", "Asia/Baku"),
                    ("Asia/Yakutsk", "Asia/Yakutsk"),
                    ("Europe/Belfast", "Europe/Belfast"),
                    ("Pacific/Auckland", "Pacific/Auckland"),
                    ("America/Kralendijk", "America/Kralendijk"),
                    ("Pacific/Palau", "Pacific/Palau"),
                    ("Asia/Taipei", "Asia/Taipei"),
                    ("America/St_Barthelemy", "America/St_Barthelemy"),
                    ("America/Port_of_Spain", "America/Port_of_Spain"),
                    ("Brazil/East", "Brazil/East"),
                    ("Asia/Thimbu", "Asia/Thimbu"),
                    ("Africa/Gaborone", "Africa/Gaborone"),
                    ("America/Noronha", "America/Noronha"),
                    ("Etc/GMT+3", "Etc/GMT+3"),
                    ("America/Indiana/Winamac", "America/Indiana/Winamac"),
                    ("Universal", "Universal"),
                    ("Europe/London", "Europe/London"),
                    ("Asia/Tbilisi", "Asia/Tbilisi"),
                    ("America/Edmonton", "America/Edmonton"),
                    ("America/Anguilla", "America/Anguilla"),
                    ("America/Mazatlan", "America/Mazatlan"),
                    ("America/La_Paz", "America/La_Paz"),
                    ("Pacific/Norfolk", "Pacific/Norfolk"),
                    ("Asia/Irkutsk", "Asia/Irkutsk"),
                    ("PRC", "PRC"),
                    ("Etc/GMT+10", "Etc/GMT+10"),
                    ("America/Puerto_Rico", "America/Puerto_Rico"),
                    ("Asia/Colombo", "Asia/Colombo"),
                    ("ROK", "ROK"),
                    ("Asia/Ulan_Bator", "Asia/Ulan_Bator"),
                    ("America/Ciudad_Juarez", "America/Ciudad_Juarez"),
                    ("Africa/Djibouti", "Africa/Djibouti"),
                    ("Australia/West", "Australia/West"),
                    ("Africa/Addis_Ababa", "Africa/Addis_Ababa"),
                    ("America/Argentina/San_Juan", "America/Argentina/San_Juan"),
                    ("Europe/Isle_of_Man", "Europe/Isle_of_Man"),
                    ("Asia/Atyrau", "Asia/Atyrau"),
                    ("GB", "GB"),
                    ("Navajo", "Navajo"),
                    ("America/Santa_Isabel", "America/Santa_Isabel"),
                    ("Hongkong", "Hongkong"),
                    ("Pacific/Truk", "Pacific/Truk"),
                    ("Europe/Vilnius", "Europe/Vilnius"),
                    ("Japan", "Japan"),
                    ("Asia/Almaty", "Asia/Almaty"),
                    ("Etc/GMT+11", "Etc/GMT+11"),
                    ("Africa/Conakry", "Africa/Conakry"),
                    ("Asia/Amman", "Asia/Amman"),
                    ("Atlantic/Azores", "Atlantic/Azores"),
                    ("America/Blanc-Sablon", "America/Blanc-Sablon"),
                    ("America/Belize", "America/Belize"),
                    ("Europe/Brussels", "Europe/Brussels"),
                    ("Europe/San_Marino", "Europe/San_Marino"),
                    ("Africa/Nairobi", "Africa/Nairobi"),
                    ("Asia/Pyongyang", "Asia/Pyongyang"),
                    ("Asia/Jayapura", "Asia/Jayapura"),
                    ("Australia/Queensland", "Australia/Queensland"),
                    ("America/Dominica", "America/Dominica"),
                    ("Indian/Mayotte", "Indian/Mayotte"),
                    ("US/Samoa", "US/Samoa"),
                    ("America/Fort_Wayne", "America/Fort_Wayne"),
                    ("America/St_Johns", "America/St_Johns"),
                    ("PST8PDT", "PST8PDT"),
                    ("Jamaica", "Jamaica"),
                    ("America/Lima", "America/Lima"),
                    ("America/Sitka", "America/Sitka"),
                    ("Asia/Tashkent", "Asia/Tashkent"),
                    ("ROC", "ROC"),
                    ("Africa/Mbabane", "Africa/Mbabane"),
                    ("America/Dawson", "America/Dawson"),
                    ("Asia/Saigon", "Asia/Saigon"),
                    ("Pacific/Tarawa", "Pacific/Tarawa"),
                    ("Mexico/BajaSur", "Mexico/BajaSur"),
                    ("Australia/Sydney", "Australia/Sydney"),
                    ("America/Denver", "America/Denver"),
                    ("Pacific/Ponape", "Pacific/Ponape"),
                    ("Iceland", "Iceland"),
                    ("America/Chihuahua", "America/Chihuahua"),
                    ("Africa/Ndjamena", "Africa/Ndjamena"),
                    ("America/Mendoza", "America/Mendoza"),
                    ("Europe/Guernsey", "Europe/Guernsey"),
                    ("America/Paramaribo", "America/Paramaribo"),
                    ("Etc/GMT-3", "Etc/GMT-3"),
                    ("EST5EDT", "EST5EDT"),
                    ("MST7MDT", "MST7MDT"),
                    ("Asia/Tomsk", "Asia/Tomsk"),
                    ("America/Rio_Branco", "America/Rio_Branco"),
                    ("America/Montreal", "America/Montreal"),
                    ("America/Yakutat", "America/Yakutat"),
                    ("Africa/El_Aaiun", "Africa/El_Aaiun"),
                    ("GB-Eire", "GB-Eire"),
                    ("America/North_Dakota/Center", "America/North_Dakota/Center"),
                    ("Africa/Luanda", "Africa/Luanda"),
                    ("Australia/Yancowinna", "Australia/Yancowinna"),
                    ("Africa/Kinshasa", "Africa/Kinshasa"),
                    ("EET", "EET"),
                    ("America/Nassau", "America/Nassau"),
                    ("Pacific/Wake", "Pacific/Wake"),
                    ("America/Rankin_Inlet", "America/Rankin_Inlet"),
                    ("Australia/Currie", "Australia/Currie"),
                    ("UTC", "UTC"),
                    ("Asia/Kuala_Lumpur", "Asia/Kuala_Lumpur"),
                ],
                default="America/Denver",
                max_length=256,
            ),
        ),
        migrations.RunPython(update_timezones),
    ]
