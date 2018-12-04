"""
Apache Test Fixture

This fixture doesn't do any setup, but verifies that the created service is
running default apache.
"""
import requests
import consul
from cloudless.testutils.blueprint_tester import call_with_retries
from cloudless.testutils.fixture import BlueprintTestInterface, SetupInfo
from cloudless.types.networking import CidrBlock

RETRY_DELAY = float(10.0)
RETRY_COUNT = int(10)

class BlueprintTest(BlueprintTestInterface):
    """
    Fixture class that creates the dependent resources.
    """
    def setup_before_tested_service(self, network):
        """
        Create the dependent services needed to test this service.
        """
        # Since this service has no dependencies, do nothing.
        return SetupInfo({}, {})

    def setup_after_tested_service(self, network, service, setup_info):
        """
        Do any setup that must happen after the service under test has been
        created.
        """
        my_ip = requests.get("http://ipinfo.io/ip")
        test_machine = CidrBlock(my_ip.content.decode("utf-8").strip())
        self.client.paths.add(test_machine, service, 8500)

    def verify(self, network, service, setup_info):
        """
        Given the network name and the service name of the service under test,
        verify that it's behaving as expected.
        """
        def check_consul_setup():
            public_ips = [i.public_ip for s in service.subnetworks for i in s.instances]
            assert public_ips, "No services are running..."
            for public_ip in public_ips:
                consul_client = consul.Consul(public_ip)
                assert consul_client.kv.put('testkey', 'testvalue'), "Failed to put test key!"
                testvalue = consul_client.kv.get('testkey')
                assert testvalue[1]["Key"] == "testkey"
                consul_client.kv.delete('testkey')
        call_with_retries(check_consul_setup, RETRY_COUNT, RETRY_DELAY)
