# Teaching Principles

## The Four Truths of Effective Teaching

### 1. Mental Models, Not Procedures

**Weak** (procedures):
```
Step 1: Import the library
Step 2: Initialize the client
Step 3: Call the function
Step 4: Handle the response
```

**Strong** (mental model):
```
Think of an API client like a waiter at a restaurant.
You (the code) tell the waiter (client) what you want.
The waiter goes to the kitchen (server) and brings back food (response).
Sometimes the kitchen is busy (rate limits) or out of ingredients (errors).

Now you understand WHY you need error handling - it's not just "best practice",
it's because kitchens run out of things.
```

The difference: procedures tell WHAT to do, mental models explain HOW to think.


### 2. Real Examples, Not Abstract

**Weak** (abstract):
```
Consider a scenario where you need to cache expensive computations.
You might use memoization to store results.
```

**Strong** (real):
```
Look at your gemini-imagegen project. Every time you call the API,
it costs money and takes 3 seconds. You're calling it repeatedly
with the same prompts during development.

Here's how to add caching to YOUR code:
[actual code from their project with modifications]
```

The learner's own project is always more memorable than hypotheticals.


### 3. Show the Journey

**Weak** (just the answer):
```
Use a hash map for O(1) lookup.
```

**Strong** (the journey):
```
Your first instinct might be a list - loop through, find the match.
Works fine for 10 items.

But you have 10,000 items. Now each lookup scans 10,000 entries.
Your API response time goes from 50ms to 2 seconds.

The insight: What if you could jump directly to the item?
That's what a hash map does - it converts the key to a location.

Now O(1) isn't just "faster" - you understand WHY it's faster.
```


### 4. One Deep > Ten Shallow

**Weak** (ten shallow):
```
Today we'll cover:
- Variables
- Functions
- Classes
- Inheritance
- Polymorphism
- Decorators
- Context managers
- Generators
- Async/await
- Metaclasses
```

**Strong** (one deep):
```
Today: Generators. Just generators. We'll understand them completely.

By the end, you'll know:
- The problem they solve (memory)
- How they work (yield pauses execution)
- When to use them (streaming, large datasets)
- When NOT to use them (random access needed)
- How they connect to what you already know (iterators)

And you'll have refactored one function in YOUR code to use them.
```


## Common Teaching Anti-Patterns

### The Info Dump
Giving all information at once instead of building understanding progressively.

### The Assumed Context
Using jargon or concepts the learner hasn't encountered yet.

### The Missing Why
Explaining what to do without explaining why it matters.

### The Generic Example
Using foo/bar/baz instead of real code from the learner's projects.

### The Perfectionist
Teaching the "right" way before the learner understands the problem.


## Calibration by Experience Level

**Beginner:**
- More analogies
- Slower pace
- Explicit connections to prior knowledge
- More scaffolding

**Intermediate:**
- Focus on mental models
- Show trade-offs
- Challenge assumptions
- Less hand-holding

**Advanced:**
- Discuss edge cases
- Compare approaches
- Reference shared history
- Move faster, go deeper
