# stop non-critical services (windows)

import psutil

#critical_services = ["wuauserv", "wscsvc", "bits"]


def get_running_services():
    running_services = []

    for service in psutil.win_service_iter():
        service_info = service.as_dict()
        running_services.append(service_info)

    return running_services


# def stop_non_critical_services(critical_services, running_services):
#     for service in running_services:
#         service_name = service['name']
#         if service_name not in critical_services:
#             try:
#                 service_obj = psutil.win_service_get(service_name)
#                 service_obj.stop()
#                 print(f"Stopped non-critical service: {service_name}")
#             except Exception as e:
#                 print(f"Failed to stop service {service_name}: {str(e)}")


if __name__ == "__main__":
    services = get_running_services()
    for service in services:
        print(f"Service Name: {service['name']}")
        print(f"Display Name: {service['display_name']}")
        print(f"Status: {service['status']}")
        print(f"Start Type: {service['start_type']}\n")
    #stop_non_critical_services(critical_services, services)
