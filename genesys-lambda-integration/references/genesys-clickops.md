# Genesys Cloud Data Action ClickOps Setup

## Prerequisites

- Terraform applied (`tfa`) — `genesys_cloud_role_arn` output value ready to paste
- Lambda deployed and tested in the AWS console (test event `{}`, confirm JSON object response)

---

## Step 1 — Add the AWS Lambda Integration

1. Admin → Integrations → **+ Add Integration**
2. Search for **Amazon Web Services Lambda** → Install
3. Under **Credentials** → Role ARN: paste the `genesys_cloud_role_arn` Terraform output value
4. **Save & Activate**
5. If the status doesn't flip to Active automatically, click the Status toggle → Confirm

---

## Step 2 — Create the Data Action

1. Under the integration → **Actions** tab → **+ Add Action**
2. Name it descriptively (e.g. `Generate OTP`, `Lookup Account`)

### Configuration Tab

| Field | Value |
|---|---|
| Request URL Template | Lambda ARN (e.g. `arn:aws:lambda:us-west-2:149536452996:function:pin_generator`) |
| Request Type | `POST` |
| Request Body | `{}` (empty for no-input Lambdas, or JSON with input fields) |

### Contracts Tab — Output Contract

Add one property per field returned by the Lambda JSON response:

| Property Name | Type | Notes |
|---|---|---|
| `OTP` | String | Must match JSON key exactly — case-sensitive |

No success template is needed when the Lambda returns a proper JSON object.

### Test the Data Action

- Click the **Test** tab
- Hit **Run** — confirm the response shows the expected named field (e.g. `{"OTP":"042817"}`)
- If the response shows the value but the output contract shows no result, the Lambda is returning a plain string — update it to return a JSON object

### Publish

- Click **Save** then **Publish**
- Unpublished actions are not available in Scripts or Architect flows

---

## Step 3 — Create the Agent Script

1. Admin → **Scripts** → **New Script**

### Add a Button (triggers the Lambda)

- Add a **Button** component to the script canvas
- Set the button label (e.g. `Generate OTP`)
- On Click action: **Call Data Action**
- Select the Data Action created above
- Map any input variables if the Lambda takes input

### Add a Display Field (shows the result)

- Add a **Label** or **Text** component
- Bind its value to the Data Action output variable (e.g. `OTP`)
- This will display the value after the button is clicked

### Publish & Assign

- **Publish** the script
- Assign it to the relevant queue or wrap-up code under Admin → Contact Center → Scripts

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Data Action test shows value but output contract is empty | Lambda returning plain string | Update Lambda to return JSON object with named field |
| "expects an object" in output contract UI | Trying to map schema before success template set, OR Lambda not returning object | Ensure Lambda returns `{"field":"value"}` |
| Integration shows credentials error | Role ARN wrong or Genesys org ID mismatch in ExternalId | Verify `genesys_cloud_role_arn` output and `var.genesys_org_id` |
| Data Action not available in Script | Action not published | Publish the action |
| Role assumption fails | Wrong Genesys AWS account ID for your region | Check region in `references/iam.md` |
