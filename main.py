import time
from prometheus_client.core import GaugeMetricFamily, CounterMetricFamily, REGISTRY
from prometheus_client import start_http_server
from prometheus_client.metrics_core import GaugeMetricFamily, CounterMetricFamily
from requests.auth import HTTPBasicAuth
import requests
import os


class Session:
    def __init__(self, vmware_hcx_ip, vmware_hcx_id, vmware_hcx_pw):
        self._vmware_hcx_ip = vmware_hcx_ip
        self._vmware_hcx_id = vmware_hcx_id
        self._vmware_hcx_pw = vmware_hcx_pw
        self.url = "https://" + self._vmware_hcx_ip + "/hybridity/api/"
        self.payload = {}
        self.headers = {
            'Content-Type': 'application/json',
        }

    def get_token(self):
        url = self.url + "sessions/"
        self.payload["username"] = self._vmware_hcx_id
        self.payload["password"] = self._vmware_hcx_pw
        response = requests.request("POST", url, verify=False, headers=self.headers, data=self.payload,
                                    )
        return response.headers["x-hm-authorization"]


class Client(Session):
    def __init__(self):
        Session.__init__(self, os.environ.get("VMWARE_HCX_IP"), os.environ.get("VMWARE_HCX_ID"),
                         os.environ.get("VMWARE_HCX_PW"))
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Basic '
        }
        self.token = self.get_token()

    def render_get(self, prefix: str, body: dict):
        headers = self.headers
        url = self.url + prefix
        ssl_verify = os.environ.get("SSL_VERIFY")
        body["x-hm-authorization"] = self.token
        response = requests.request("GET", url, headers=headers, body=body,
                                    verify=bool(ssl_verify))
        return response

    def render_post(self, prefix: str, body: dict):
        headers = self.headers
        url = self.url + prefix
        ssl_verify = os.environ.get("SSL_VERIFY")
        body["x-hm-authorization"] = self.token
        response = requests.request("POST", url, headers=headers, body=body,
                                    verify=bool(ssl_verify))
        return response

    def get_tasks(self, state: str):
        body = {"filter": {"status": state}}
        response = self.render_post(prefix="interconnect/tasks/", body=body)
        tasks = response['items']
        return tasks

    def get_steps(self):
        response = self.render_get(prefix="steps/", body={})
        tasks = response['items']
        return tasks

    def get_alerts(self, severity: str):
        body = {"filter": {"severity": severity}}
        response = self.render_post(prefix="alerts/", body=body)
        tasks = response['items']
        return tasks


class myCustomCollector(object):
    def __init__(self):
        self.client = Client()

    def collect(self):
        metric_list = {}
        metric_list['tasks'] = GaugeMetricFamily("number_of_task", "Count Of Tasks by Status",
                                                  labels=["status"])
        running_tasks = self.client.get_tasks(state="RUNNING")
        failed_tasks = self.client.get_tasks(state="FAILED")
        success_tasks = self.client.get_tasks(state="SUCCESS")
        queued_tasks = self.client.get_tasks(state="QUEUED")
        task_metric = metric_list['tasks']
        task_metric.add_metric(["queued"], len(queued_tasks))
        task_metric.add_metric(["failed"], len(failed_tasks))
        task_metric.add_metric(["runnning"], len(running_tasks))
        task_metric.add_metric(["succeed"], len(success_tasks))
        yield metric_list['tasks']

        # metric_list['step'] = GaugeMetricFamily()
        # yield metric_list['step']

        critical_alerts = self.client.get_tasks(state="RUNNING")
        warning_alerts = self.client.get_tasks(state="FAILED")
        info_alerts = self.client.get_tasks(state="SUCCESS")

        metric_list['alert'] = GaugeMetricFamily("number_of_alert", "Count Of Alerts by Severity",
                                                  labels=["severity"])
        alert_metric = metric_list['alert']
        alert_metric.add_metric(["critical"], len(critical_alerts))
        alert_metric.add_metric(["warning"], len(warning_alerts))
        alert_metric.add_metric(["info"], len(info_alerts))
        yield metric_list['alert']


if __name__ == "__main__":
    port = 9000
    frequency = 5
    start_http_server(port)
    REGISTRY.register(myCustomCollector())

    while True:
        time.sleep(frequency)
