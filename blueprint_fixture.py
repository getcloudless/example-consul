"""
Apache Test Fixture

This fixture doesn't do any setup, but verifies that the created service is
running default apache.
"""
import requests
import hvac
from cloudless.testutils.blueprint_tester import call_with_retries
from cloudless.testutils.fixture import BlueprintTestInterface, SetupInfo
from cloudless.types.networking import CidrBlock

RETRY_DELAY = float(10.0)
RETRY_COUNT = int(6)

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
        self.client.paths.add(test_machine, service, 8200)
        self.client.paths.add(test_machine, service, 8201)

    def verify(self, network, service, setup_info):
        """
        Given the network name and the service name of the service under test,
        verify that it's behaving as expected.
        """
        def check_vault_setup():
            public_ips = [i.public_ip for s in service.subnetworks for i in s.instances]
            assert public_ips, "No services are running..."
            for public_ip in public_ips:
                shares = 1
                threshold = 1
                client = hvac.Client(url='http://%s:8200' % public_ip)
                result = client.initialize(shares, threshold)
                root_token = result['root_token']
                keys = result['keys']
                client.unseal_multi(keys)
                logged_in_client = hvac.Client(url='http://%s:8200' % public_ip, token=root_token)
                logged_in_client.write('secret/foo', baz='bar', lease='1h')
                my_secret = logged_in_client.read('secret/foo')
                logged_in_client.delete('secret/foo')
                assert "baz" in my_secret["data"], "Baz not in my_secret: %s" % my_secret
                assert my_secret["data"]["baz"] == "bar", "Baz not 'bar': %s" % my_secret
        call_with_retries(check_vault_setup, RETRY_COUNT, RETRY_DELAY)
