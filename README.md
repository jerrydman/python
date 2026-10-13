# Python Scripts

Python scripts I've written to help me do my job, mostly AWS cloud operations and automation, plus a few personal projects and network experiments.

## Setup

```bash
python3 -m venv myenv && source myenv/bin/activate
pip install boto3 prettytable requests python-dotenv discord.py scapy twilio pyttsx3 openai dnspython python-dateutil
```

Most AWS scripts use a named profile from `~/.aws/credentials`:

```bash
python3 <script>.py --profile <profile>
```

Secrets (Discord tokens, API keys, etc.) come from environment variables or a `.env` file. Never hardcode them. Run any script with `-h` or read its header comments for options.

## AWS inventory and auditing

| Script | Description |
|---|---|
| `Ec2Inventory.py` | Lists EC2 instances in every region of an account as a table. |
| `EC2InventoryTagvCPU.py` | EC2 instance and vCPU counts grouped by `TechnologyCode` tag, by region, with totals. Can export CSV. |
| `InstanceVerification.py` | Finds EC2 instances with a given tag key/value and reports their instance profile ARNs. |
| `UnattachedEBS.py` | Finds unattached EBS volumes across all regions. |
| `IamUsers.py` / `iam_users.py` | Reports IAM users and their access key details (JSON output). |
| `IamUsersTag.py` | Same as above, with tag information. |
| `promptdist.py` | Scans IAM users for a distribution-list tag and prompts for a value on any that lack it. |
| `bulktagrds.py` | Adds a tag to all RDS instances in a region. |
| `githubAuditLog.py` | Checks the GitHub org audit log for `protected_branch_override` events. |

## Secrets and credential rotation

| Script | Description |
|---|---|
| `getSecrets3.py` | Fetches a secret from AWS Secrets Manager (pipe to `jq` to pull fields). |
| `CrossAcctSecret.py` | Reads a secret in another account by assuming a role (Lambda-style). |
| `keySecret3.py` / `rotateKeys3.py` | Rotate IAM access keys and store the new ones in Secrets Manager. |
| `Rotate3KeyLambda.py` | Lambda that rotates keys, reading the username and SNS topic from tags. |
| `PasswordRotate.py` | Generates a new random password, updates Secrets Manager, and produces a salted SHA-512 hash for Linux shadow files. |
| `PasswordRotate3_email_slack.py` | Password rotation that keeps the username and sends email/Slack notifications. |
| `RotateUserNamePassword3.py` | Rotates the password in a JSON-formatted secret and keeps the username. |
| `getroot.py`, `getrootTEST.py`, `getpasswordonly.py`, `updateroot.py` | Fetch and update hashed root passwords in Secrets Manager. |

## AWS infrastructure and notifications

| Script | Description |
|---|---|
| `UpdateTargetGroupRDS.py` | Updates an ALB target group with the RDS endpoint's current IPs (DNS lookup). Imports `elbv2_client` and `tg_utils`, which are not in this repo. |
| `DeleteSelectedUsersSFTP.py` | Deletes selected users from an AWS Transfer (SFTP) server. |
| `googlechat-lambda.py` | Lambda that posts messages to Google Chat. |
| `sendmail3.py` | Sends email over SMTP. |
| `agent/agent.py` | Google ADK agent that uses the AWS CloudWatch and Terraform MCP servers (via `uvx`) to monitor AWS infrastructure. |

## Bots and personal projects

| Script | Description |
|---|---|
| `SocialFix.py` | Discord bot that replaces Instagram and TikTok links with embed-friendly ones. Needs a Discord token in `.env`. |
| `ftp.py` / `ftpmobileupdated.py` | Discord bot that replies with a GIF when a message mentions Packers-related terms (also checks embeds). Token comes from the `discordtoken` environment variable. |
| `peloton.py` | Calculates yearly running and cycling totals from the Peloton API. |
| `cvsvax.py` | Polls the CVS COVID-19 vaccine page every 60 seconds and texts via Twilio when Massachusetts appointments open (needs a Twilio account; likely obsolete). |
| `bingo.py` | Bingo caller with text-to-speech and a table display. |
| `openAI/pythonai.py` | Minimal OpenAI API test. |

## Network experiments

| Script | Description |
|---|---|
| `80211listening.py` | Scapy sniffer that lists new 802.11 probe requests (Python 2 syntax). |
| `creditsniff.py` | Scapy packet sniffer that matches credit-card-number patterns. For lab/educational use only. |
| `netmikoTest.py` | Netmiko stub. |

## Notes

- `ignore/` and `*.xml` are git-ignored. `myenv/` is a local virtualenv that is not in `.gitignore`; consider adding it.
- Several scripts have placeholders (such as `$profile`, empty credentials) that need editing before use.
- Many scripts touch production AWS resources (key and password rotation, deletes). Test with a non-production profile first.
