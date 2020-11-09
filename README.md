# Programming Club Backend

## Table of Contents

[Documentation](#documentation)

- [Forum](#forum)
  - [`/forum` GET](#forum-get)
  - [`/forum/posts` GET](#forumposts-get)
- [User](#user)
  - [`/auth` POST](#auth-post)
  - [`/user` GET](#user-get)

## Documentation

Credentials should always be sent with the requests if exist, and accepted from the responses.

The response object for each API is referenced by the `data` property of a JSON object that also contains `success` and `message` properties. The former indicates if the request is successful and the latter is a string describing the `success` property (usually empty unless the request is unsuccessful).

- Syntax

  ```typescript
  {
    "data": Object, // the response object
    "message": string,
    "success": boolean
  }
  ```

### Forum

#### `/forum` GET

Fetch forum categories and blocks.

**Parameters**

None

**Response**

```typescript
{
  /**
   * `categories` object contains number keys,
   * each is associated with an object that represent
   * the category
   */
  "categories": {
    /**
     * category 0 only has the `blocks` property
     * that contains uncategorized blocks
     */
    "0": {
      /**
       * an array every catagory object has that is
       * of all blocks that this category contains
       */
      "blocks": [
        {
          "bid": number,
          "category": null | number, // category id
          "description": string,
          "icon": string, // url
          "name": string
        },
        ...
      ]
    },
    /**
     * category 1 and on all have the `id` and `name`
     * properties
     */
    "1": {
      "blocks": [
        ...
      ],
      "id": number, // category id
      "name": string
    },
    ...
  }
}
```

#### `/forum/posts` GET

Fetch forum posts.

**Parameters**

Optional

- `block` (int): get posts associated with a specific block id, default `0` (all posts)
- `page` (int): the page number, default `1`
- `size` (int): the size of the page (number of posts per page), default: `32`

**Response**

```typescript
{
  /**
   * the total amount of posts, only returned when
   * `block` is `0`
   */
  "count": number,

  /**
   * an array of all posts or posts from a block
   * specified by the `block` parameter, with the size
   * set by the `size` (page size) parameter and the
   * offset of (`page` * `size` + 1), starting from the
   * latest commented post
   */
  "posts": [
    {
      "author": number, // user id (uid)
      "block": number,
      "content": string,
      "creation_time": number, // utc timestamp
      "latest_comment": number, // utc timestamp
      "pid": number, // post id
      "title": string
    },
    ...
  ]
}
```

### User

#### `/auth` POST

Establish a new session or *renew the existing session* (existing sessions are renewed automatically, DO NOT USE this api if that is the only purpose).

**Parameters**

Required (form)

- `token` (string): the id token that is provided by Google Auth

**Response**

```typescript
{
  /**
   * a boolean indicating if the user is
   * new to the forum (true) or already has an
   * account (false)
   */
  "newbie": boolean
}
```

#### `/user` GET

Fetch the public information of a user.

**Parameters**

Optional

- `uid` (int): a specific user id or `0` for the current session user if `name` is `""`, default `0`
- `name` (string): a user name, accepted if `uid` is `0`, default `""`
- `code` (int): a user code, accepted if `uid` is `0` and `name` is not `""`, default `0`
- `userpage` (bit): whether to include the user page text in the response (`1`) or not (`0`), default `0`

**Response**

```typescript
{
  "bio": string, // markdown
  "code": number,
  "email": string,
  "exp": number,
  "is_member": 0 | 1,
  "is_moderator": 0 | 1,
  "join_time": null | number, // utc timestamp
  "lv": {
    "color": string, // hex color code
    "id": number,
    "name": string,
    "text_color": null | string // hex color code
  },
  "name": string,
  "picture": string, // url
  "register_time": number, // utc timestamp
  "user_page": string, // markdown, if `userpage` is `1`
  "uid": number, // uid
  "verify": null | {
    "color": string, // hex color code
    "id": number,
    "message": string,
    "tag": string,
    "text_color": null | string // hex color code
  }
}
```
