import requests
import yaml
import json
import os
import amplitude
import utils
import datetime
from ua_parser import user_agent_parser

headers = {"Content-Type": "application/json", "Accept": "*/*"}

r = requests.post("https://api.amplitude.com/2/httpapi", params={}, headers=headers)


class Amplitude_user:
    def __init__(self):
        pass

    def gen_user(self, current_server_session):
        if os.getenv("IS_DEV").upper() == "FALSE":
            self.current_server_session = current_server_session

            # Generate the current user on the page as our Amplitude User Object
            data = utils.parse_headers(current_server_session.ws.request)
            user_data = {"has_precise_ip": False}
            if "user_public_data" in data["Cookie"].keys():
                for key in data["Cookie"]["user_public_data"].keys():
                    user_data[key] = data["Cookie"]["user_public_data"][key]
                user_data["has_precise_ip"] = True
            else:
                user_data["ip"] = data["Remote_ip"]
            if "user_unique_id" in data["Cookie"].keys():
                user_data["user_id"] = data["Cookie"]["user_unique_id"]
            else:
                user_data["user_id"] = "unknown_user_placeholder"
            for inkey in data.keys():
                if inkey[:3] == "ua_":
                    user_data[inkey] = data[inkey]

            self.key = os.getenv("AMPLITUDE_KEY")
            self.user_data = user_data

    def log_event(self, event, event_args=dict()):
        """
         To be called directly only in areas with no external reruns
         like inside buttons for example.
         For other circumstances use the safe version.
        """
        if os.getenv("IS_DEV").upper() == "FALSE":
            # print("logging : " + event + " at " + str(datetime.datetime.now()))
            event_data = {
                "user_id": self.user_data["user_id"],
                "event_type": event,
                "event_properties": event_args,
                "ip": self.user_data["ip"],
                # "device_id": self.user_data["user_id"],
            }
            request_data = dict()
            if self.user_data["has_precise_ip"]:
                event_data["dma"] = self.user_data["city"]
                event_data["country"] = self.user_data["country_name"]
                event_data["region"] = self.user_data["region"]
                event_data["city"] = self.user_data["city"]
                event_data["location_lat"] = self.user_data["latitude"]
                event_data["location_lng"] = self.user_data["longitude"]
                event_data["carrier"] = self.user_data["isp"]
            for inkey in self.user_data.keys():
                if inkey[:3] == "ua_":
                    event_data[inkey[3:]] = self.user_data[inkey]
            request_data["api_key"] = self.key
            request_data["events"] = [event_data]
            response = requests.post(
                "https://api.amplitude.com/2/httpapi", json=request_data, headers=headers
            )
            # print(request_data)
            # print(response.json())
            return response.json()

    def safe_log_event(  # For use in areas subject to various reruns
        self,
        event,
        session_state,
        event_args=dict(),
        is_new_page=False,
        alternatives=[],
    ):
        """
        Receives the call for an event but decides if the event is worth logging or not by using our session makeshift db.
        This is to avoid us logging multiple times the same event when the page reloads.
        If the item is inside a button you can use the normal version, but otherwise it is recommended to use this one.

        is_new_page is a boolean telling if this event is the user moving to a new page, in which case the code
        will detect if this event is not repeated and then if it is not it will reset all the other values and log the page change.

        alternatives is a list of alternate events that could have happened instead of this one (for example when choosing a a scenario
        in simulacovid). This is such that we can keep track of what option is chosen at the current moment by making the chosen option
        True and the rest False.

        For the rest of the events it will try to use the event_args object and detect any changes from the previous ones.
        If a change is detected it will log the event, if not it will ignore.

        Alternatively it can trigger empty event_args events by checking if it is True or False, if it is False then we log and
        make it True. If it is True we ignore."""
        if os.getenv("IS_DEV").upper() == "FALSE":
            if session_state.amplitude_events is None:
                session_state.amplitude_events = dict()
                session_state.old_amplitude_events = dict()
            if (
                is_new_page
            ):  # If it is the opening of a new page we only register the event if the opening is really new
                if (
                    event not in session_state.old_amplitude_events.keys()
                    or session_state.old_amplitude_events[event] is not True
                ):  # If the page wasnt opened before or is brand new event
                    for (
                        key
                    ) in session_state.old_amplitude_events.keys():  # Reset the old dict
                        session_state.old_amplitude_events[key] = None
                    session_state.old_amplitude_events[
                        event
                    ] = True  # Say that he have opened the page
                    session_state.amplitude_events[
                        event
                    ] = True  # Say that we will keep it open
                    self.log_event(event, event_args)  # Log the event
            else:  # If it is not a new page we have to check for differences in the state
                if (
                    event not in session_state.old_amplitude_events.keys()
                    # If the event is brand new
                    or (
                        session_state.old_amplitude_events[event] is None
                        # If the event had been reseted
                        or session_state.old_amplitude_events[event] is False
                        # If the even was inactive or not chosen
                        or (
                            session_state.old_amplitude_events[event] not in [True, False]
                            and session_state.old_amplitude_events[event] != event_args
                        )
                    )  # If the event has been changed
                ):
                    self.log_event(event, event_args)  # Log the event
                    if len(event_args.keys()) == 0:  # If the event comes in empty
                        session_state.amplitude_events[event] = True
                    else:  # Else we save the relevant data to look for changes later
                        session_state.amplitude_events[event] = event_args
                    for alternative in alternatives:
                        # If we have alternatives we must make sure to mark them all as not chosen
                        if alternative != event:
                            session_state.amplitude_events[alternative] = False

    def conclude_user_session(
        self, session_state
    ):  # Once we finish loading it all turn the old into new
        """ 
        This function is essential for pages that have multiple amplitude events that can trigger reruns.
        If your page does more than logging at loading, it should add this to the end of the page so that
        when we load the entire page we can make sure to make throw the current values into the old values object
        and begin a new one. This means effectively updating our manager saying that the entire page loaded sucessfully
        and that now we should look into the future.
        """
        if os.getenv("IS_DEV").upper() == "FALSE":
            session_state.old_amplitude_events = dict(session_state.amplitude_events)

