# Lambda Response Patterns for Genesys Cloud

## Why a JSON Object Is Required

Genesys Cloud Data Actions bind Lambda output to named variables. A plain string has no key name, so Genesys can display it but cannot expose it as a variable in Scripts or Architect flows. Always return a struct/object with named fields.

## Go — Single Value Response

```go
// Response is the JSON object returned to Genesys Cloud Data Actions.
// Field names in the json tag become the output variable names in Genesys.
type Response struct {
    OTP string `json:"OTP"`
}

func handler() (Response, error) {
    value, err := generateValue()
    if err != nil {
        return Response{}, err
    }
    return Response{OTP: value}, nil
}
```

**Lambda returns:** `{"OTP":"042817"}`
**Genesys output contract:** Add property `OTP` → `String`

## Go — Multiple Values Response

```go
type Response struct {
    AccountNumber string `json:"accountNumber"`
    Balance       string `json:"balance"`
    Status        string `json:"status"`
}

func handler(req Request) (Response, error) {
    // ... lookup logic
    return Response{
        AccountNumber: acct.Number,
        Balance:       acct.Balance,
        Status:        acct.Status,
    }, nil
}
```

**Genesys output contract:** Add properties `accountNumber`, `balance`, `status` — each as `String`.

## Go — With Input from Genesys

Genesys sends the Data Action request body as the Lambda event payload.

```go
type Request struct {
    CustomerID string `json:"customerId"`
}

type Response struct {
    Name  string `json:"name"`
    Email string `json:"email"`
}

func handler(req Request) (Response, error) {
    // req.CustomerID is populated from the Genesys Data Action request body
}
```

**Genesys input contract:** Add property `customerId` → `String`
**Data Action request body:** `{"customerId": "${input.customerId}"}`

## Naming Conventions

- Use camelCase for multi-word fields: `accountNumber`, `customerName`
- Use ALL_CAPS for acronyms: `OTP`, `PIN`  
- Field names are case-sensitive in Genesys — output contract property names must match the JSON tag exactly
- Keep field names short — they become variable names agents see in Scripts

## Error Handling

Return a Go error for Lambda-level failures. Genesys will route to the Data Action failure path.

```go
func handler() (Response, error) {
    value, err := generate()
    if err != nil {
        return Response{}, fmt.Errorf("generation failed: %w", err)
    }
    return Response{Value: value}, nil
}
```
