'''
Copyright (c) 2020 Cisco and/or its affiliates.

This software is licensed to you under the terms of the Cisco Sample
Code License, Version 1.1 (the "License"). You may obtain a copy of the
License at

               https://developer.cisco.com/docs/licenses

All use of the material herein must be in accordance with the terms of
the License. All rights not expressly granted by the License are
reserved. Unless required by applicable law or agreed to separately in
writing, software distributed under the License is distributed on an "AS
IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
or implied.
'''

import yaml, requests, urllib
from flask import Flask, request, redirect, url_for, render_template
from xmltodict import parse as xml_to_dict


webex_username = None
webex_session_ticket = None
schedulingpermission_result = None
config = yaml.safe_load(open("credentials.yml"))
WEBEX_LOGIN_API_URL = "https://webexapis.com/v1"
WEBEX_MEETINGS_API_URL = "https://api.webex.com/WBXService/XMLService"


# Flask app
app = Flask(__name__)


def webex_meetings_session_ticket(webex_username, webex_access_token):
    session_ticket_xml = """
    <?xml version="1.0" encoding="UTF-8"?>
        <serv:message xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
            <header>
                <securityContext>
                    <webExID>{webex_username}</webExID>
                    <siteName>{webex_site}</siteName>
                </securityContext>
            </header>
            <body>
                <bodyContent xsi:type="java:com.webex.service.binding.user.AuthenticateUser">
                    <accessToken>{webex_access_token}</accessToken>
                </bodyContent>
            </body>
        </serv:message>
    """
    data = session_ticket_xml.format(webex_username=webex_username,
                                     webex_site=config['webex_site'],
                                     webex_access_token=webex_access_token)
    get_session_ticket = requests.post(WEBEX_MEETINGS_API_URL, data=data)
    get_session_ticket_text = xml_to_dict(get_session_ticket.text)
    global webex_session_ticket
    webex_session_ticket = get_session_ticket_text['serv:message']['serv:body']['serv:bodyContent']['use:sessionTicket']
    return webex_session_ticket


def schedulingpermission_XML(permissiongranter, permissionreceiver):
    schedulingpermission_XML_raw = """
    <?xml version="1.0" encoding="UTF-8"?>
        <serv:message xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
          <header>
            <securityContext>
                <webExID>{webex_username}</webExID>
                <sessionTicket>{webex_session_ticket}</sessionTicket>
                <siteName>{webex_site}</siteName>
            </securityContext>
          </header>
          <body>
            <bodyContent xsi:type="java:com.webex.xmlapi.service.binding.user.SetUser">
              <webExId>{permissiongranter}</webExId>
              <schedulingPermission>{permissionreceiver}</schedulingPermission>
            </bodyContent>
          </body>
        </serv:message>
    """
    schedulingpermission_XML = schedulingpermission_XML_raw.format(webex_username=webex_username,
                                                                   webex_site=config['webex_site'],
                                                                   webex_session_ticket=webex_session_ticket,
                                                                   permissiongranter=permissiongranter,
                                                                   permissionreceiver=permissionreceiver
                                                                   )
    return schedulingpermission_XML


def is_admin(webex_username):
    is_admin_xml_raw = """
    <?xml version="1.0" encoding="UTF-8"?>
    <serv:message xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
        <header>
            <securityContext>
                <webExID>{webex_username}</webExID>
                <sessionTicket>{webex_session_ticket}</sessionTicket>
                <siteName>{webex_site}</siteName>
            </securityContext>
        </header>
        <body>
            <bodyContent xsi:type="java:com.webex.service.binding.user.GetUser">
                <webExId>{webex_username}</webExId>
            </bodyContent>
        </body>
    </serv:message>
    """
    is_admin_xml = is_admin_xml_raw.format(webex_username=webex_username,
                                           webex_site=config['webex_site'],
                                           webex_session_ticket=webex_session_ticket,
                                           )
    response = requests.post(WEBEX_MEETINGS_API_URL, data=is_admin_xml)
    response_xml = xml_to_dict(response.text)
    is_admin = response_xml['serv:message']['serv:body']['serv:bodyContent']['use:privilege']['use:siteAdmin']
    return is_admin


def get_site_users():
    lstcontact_XML_body_raw = """
    <?xml version="1.0" encoding="UTF-8"?>
    <serv:message xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
        <header>
            <securityContext>
                <webExID>{webex_username}</webExID>
                <sessionTicket>{webex_session_ticket}</sessionTicket>
                <siteName>{webex_site}</siteName>
            </securityContext>
        </header>
        <body>
        <bodyContent
            xsi:type="java:com.webex.service.binding.user.LstsummaryUser">
        </bodyContent>
        </body>
    </serv:message>
    """
    LstsummaryUser_XML_body = lstcontact_XML_body_raw.format(webex_username=webex_username,
                                                             webex_site=config['webex_site'],
                                                             webex_session_ticket=webex_session_ticket,
                                                             )
    LstsummaryUser = requests.post(WEBEX_MEETINGS_API_URL, data=LstsummaryUser_XML_body)
    LstsummaryUser_xml = xml_to_dict(LstsummaryUser.text)
    users_xml = LstsummaryUser_xml['serv:message']['serv:body']['serv:bodyContent']['use:user']
    webex_site_users = []
    for user in users_xml:
        if user['use:active'] == 'ACTIVATED':
            webex_site_users.append(user['use:webExId'])

    return webex_site_users


def get_current_permissions(permissiongranter):
    get_user_xml_raw = """
    <?xml version="1.0" encoding="UTF-8"?>
    <serv:message xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
        <header>
            <securityContext>
                <webExID>{webex_username}</webExID>
                <sessionTicket>{webex_session_ticket}</sessionTicket>
                <siteName>{webex_site}</siteName>
            </securityContext>
        </header>
        <body>
            <bodyContent xsi:type="java:com.webex.service.binding.user.GetUser">
                <webExId>{permissiongranter}</webExId>
            </bodyContent>
        </body>
    </serv:message>
    """
    get_user_xml_body = get_user_xml_raw.format(webex_username=webex_username,
                                                webex_site=config['webex_site'],
                                                webex_session_ticket=webex_session_ticket,
                                                permissiongranter=permissiongranter
                                                )
    get_user = requests.post(WEBEX_MEETINGS_API_URL, data=get_user_xml_body)
    get_user_xml = xml_to_dict(get_user.text)
    try:
        current_permissions = get_user_xml['serv:message']['serv:body']['serv:bodyContent']['use:schedulingPermission']
        permissiongranter_current_permissions = current_permissions.split(";")
    except:
        permissiongranter_current_permissions = []

    return permissiongranter_current_permissions


# login page
@app.route('/')
def intranet_login():
    return render_template('mainpage_login.html', alert=None)


# login redirects to Webex for user to provide login data
@app.route('/webexlogin', methods=['POST'])
def webexlogin():
    WEBEX_USER_AUTH_URL = WEBEX_LOGIN_API_URL + "/authorize?client_id={client_id}&response_type=code&redirect_uri={redirect_uri}&response_mode=query&scope={scope}".format(
        client_id=urllib.parse.quote(config['webex_integration_client_id']),
        redirect_uri=urllib.parse.quote(config['webex_integration_redirect_uri']),
        scope=urllib.parse.quote(config['webex_integration_scope'])
        )
    return redirect(WEBEX_USER_AUTH_URL)


# based on Webex login information, a Webex access token is retrieved, a session ticket for the XML API generated, and admin privileges checked
@app.route('/webexoauth', methods=['GET'])
def webexoauth():
    webex_code = request.args.get('code')

    # to retrieve the access token
    body = {
        'client_id': config['webex_integration_client_id'],
        'code': webex_code,
        'redirect_uri': config['webex_integration_redirect_uri'],
        'grant_type': 'authorization_code',
        'client_secret': config['webex_integration_client_secret']
    }
    get_token = requests.post(WEBEX_LOGIN_API_URL + "/access_token?", headers={"Content-type": "application/x-www-form-urlencoded"}, data=body)
    webex_access_token = get_token.json()['access_token']

    # to get the username of the Webex user, here equal to email address
    global webex_username
    webex_me_details = requests.get('https://webexapis.com/v1/people/me', headers={'Authorization': 'Bearer ' + webex_access_token}).json()
    webex_username = webex_me_details['emails'][0]

    # to get a session ticket from the Webex access token and that is required for using the Webex XML API
    global webex_session_ticket
    webex_session_ticket = webex_meetings_session_ticket(webex_username, webex_access_token)

    # to reset the schedulingpermission_result variable in case the app is re-used
    global schedulingpermission_result
    schedulingpermission_result = None

    # to check if the user has site admin privileges
    check_admin = is_admin(webex_username)
    if check_admin == 'true' :
        return redirect(url_for('.mainpage'))
    else:
        return render_template('mainpage_login.html', alert=1)


# main page for the user to provide scheduling permission information
@app.route('/mainpage')
def mainpage():

    # to get all Webex users registered on the Webex Site
    webex_site_users = get_site_users()

    # to provide the relevant feedback to the user in case he/she was redirected from a previous submit (see below in submit())
    global schedulingpermission_result
    if schedulingpermission_result == None: # right after login
        return render_template('mainpage.html', webex_site_users=webex_site_users, alert=None)
    elif schedulingpermission_result == 'SUCCESS': # positive feedback after a form was submitted before
        return render_template('mainpage.html', webex_site_users=webex_site_users, alert=1)
    elif schedulingpermission_result == 'NO_PERMISSIONGRANTER': # in case no permissiongranter was selected
        return render_template('mainpage.html', webex_site_users=webex_site_users, alert=3)
    else: # negative feedback after a form was submitted before
        return render_template('mainpage.html', webex_site_users=webex_site_users, alert=2)


# to retrieve the information from the HTML form after the form is submitted to use in the subsequent API call to make the changes and to provide feedback to the user, redirects to mainpage
@app.route('/submit', methods=['POST'])
def submit():

    global schedulingpermission_result

    # to get the information from the web form and prepare it for further processing
    req = request.form
    req_radio = req.getlist("radio")

    prefix_permissiongranter = "permissiongranter-"
    permissiongranters_dict = {key:val for key, val in req.items() if key.startswith(prefix_permissiongranter)}
    permissiongranters = []
    for key in permissiongranters_dict.keys():
        short_key = key.replace("permissiongranter-", "")
        permissiongranters.append(short_key)
    if not permissiongranters:
        schedulingpermission_result = "NO_PERMISSIONGRANTER"
        return redirect(url_for('.mainpage'))

    prefix_permissionreceiver = "permissionreceiver-"
    permissionreceivers_dict = {key:val for key, val in req.items() if key.startswith(prefix_permissionreceiver)}
    permissionreceivers = []
    for key in permissionreceivers_dict.keys():
        short_key = key.replace("permissionreceiver-", "")
        permissionreceivers.append(short_key)

    # to collect feedback of API calls
    schedulingpermission_result_list = []

    # in case the permission receivers are added
    if req_radio == ['add', 'on', 'overwrite']:
        for permissiongranter in permissiongranters:
            # to collect the current permissions
            current_scheduling_permissions = get_current_permissions(permissiongranter)
            permissionreceivers.extend(current_scheduling_permissions)
            permissionreceivers_noduplicates = list(dict.fromkeys(permissionreceivers))
            if permissiongranter in permissionreceivers_noduplicates:
                permissionreceivers_noduplicates.remove(permissiongranter)
            permissionreceivers_string_add = ";".join(permissionreceivers_noduplicates)
            # API call for each permission granter
            schedulingpermission_XML_body = schedulingpermission_XML(permissiongranter, permissionreceivers_string_add)
            schedulingpermission = requests.post(WEBEX_MEETINGS_API_URL, data=schedulingpermission_XML_body)
            # to collect feedback from each API call
            schedulingpermission_xml = xml_to_dict(schedulingpermission.text)
            schedulingpermission_result_individual = schedulingpermission_xml['serv:message']['serv:header']['serv:response']['serv:result']
            schedulingpermission_result_list.append(schedulingpermission_result_individual)
    # in case the permission receivers are overwritten
    elif req_radio == ['add', 'overwrite', 'on']:
        for permissiongranter in permissiongranters:
            if permissiongranter in permissionreceivers:
                permissionreceivers.remove(permissiongranter)
            # to turn the list into a string for the API to be able to process it
            permissionreceivers_string_overwrite = ";".join(permissionreceivers)
            # API call for each permission granter
            schedulingpermission_XML_body = schedulingpermission_XML(permissiongranter, permissionreceivers_string_overwrite)
            schedulingpermission = requests.post(WEBEX_MEETINGS_API_URL, data=schedulingpermission_XML_body)
            # to collect feedback from each API call
            schedulingpermission_xml = xml_to_dict(schedulingpermission.text)
            schedulingpermission_result_individual = schedulingpermission_xml['serv:message']['serv:header']['serv:response']['serv:result']
            schedulingpermission_result_list.append(schedulingpermission_result_individual)

    # to provide overall feedback to the user (see mainpage())
    schedulingpermission_result = 'SUCCESS'
    for item in schedulingpermission_result_list:
        if item != 'SUCCESS':
            schedulingpermission_result = 'FAILED'
            break;

    return redirect(url_for('.mainpage'))


if __name__ == "__main__":
    app.run()