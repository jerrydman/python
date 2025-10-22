#DWDAY SFTP Server Python

import boto3

region = 'us-west-2'
profile = '$profile'
server = '$serverid'

def get_sftp_users(transfer_client):
    response = transfer_client.list_users(ServerId=server)

    sftp_users = []
    for user in response['Users']:
        sftp_users.append(user['UserName'])

    return sftp_users

def delete_users_except_selected(transfer_client, selected_users):
    response = transfer_client.list_users(ServerId=server)

    for user in response['Users']:
        username = user['UserName']

        # Check if the user should be deleted or kept
        if username not in selected_users:
            print(f"Deleting user: {username}")

            # # Delete the user
            transfer_client.delete_user(ServerId=server, UserName=username)

            print(f"User {username} deleted successfully.")
        else:
            print(f"Keeping user: {username}")

def main():
    # Create a Transfer client using the session
    aws_profile_name = profile
    aws_region = region
    session = boto3.Session(profile_name=aws_profile_name, region_name=aws_region)
    transfer_client = session.client('transfer')

    # List All SFTP Users
    sftp_users = get_sftp_users(transfer_client)
    print("SFTP Users:")
    for user in sftp_users:
        print(user)

    # List of users to keep (do not delete)
    selected_users = ['$userstokeep']
    delete_users_except_selected(transfer_client, selected_users)

if __name__ == "__main__":
    main()
