#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import sys


class Comm(object):
    """Handle communication of errors and events."""

    def __init__(self, script_name, recipient_list, mail_agent="mail"):
        self.mail_agent = mail_agent
        self.script_name = script_name
        self.recipient_list = recipient_list
        self.hostname = subprocess.check_output("hostname", shell=True).decode("utf-8")[
            :-1
        ]
        self.agent_present = self.is_installed(self.mail_agent)

    def send_message(self, bdy, intro="Message from ", recipient_list=""):
        address_list = recipient_list or self.recipient_list
        sbj = "{} {} on {}".format(intro, self.script_name, self.hostname)
        command = "echo '{body}'|{mailagent} -s '{subject}' {recipients}".format(
            mailagent=self.mail_agent, recipients=address_list, subject=sbj, body=bdy
        )
        if self.agent_present:
            self.run_cmd(
                sys.version[:3], command, shell=True
            )  # subprocess.run only for python >=3.5
        else:
            print(command)

    def send_error(self, err, recipientlist=""):
        self.send_message(err, "Error occured on ", recipientlist)

    @staticmethod
    def is_installed(agentname):
        man_page = subprocess.check_output(
            "man {} 2>/dev/null | wc -w".format(agentname), shell=True
        ).decode("utf-8")[:-1]
        if 0 < int(man_page):
            return True
        else:
            return False

    @staticmethod
    def run_cmd(ver, *args, **kwargs):
        if float(ver) >= 3.5:
            subprocess.run(*args, **kwargs)
        else:
            subprocess.call(*args, **kwargs)
