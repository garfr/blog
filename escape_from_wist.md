# Escape from Wist

## 11/06/21
_This article is meant to qualify [this excellent post on escape mechanisms](https://futhark-lang.org/blog/2021-06-27-no-escape.html) in the context of general purpose high-level
programming.
I recommend you read it._

## When are escape mechanisms needed?

The abstract machine of a programming language usually simplifies some aspect of the development process by limiting the
set of programs a developer can create.
For example, garbage collection (usually) removes memory management concerns at the expense of loosened control over allocation and pure languages remove
the fear of your structures being modified under your nose, leaving the developer without the tool of mutation.

Ideally, a program fit for a high-level language is organized so it can operate entirely within these bounds.
If the developer knows from the start that the program will require escaping the abstract machine the language provides, then they
probably should change to a language that provides a looser abstract machine (or one that is more fit for degenerate escape, like C).
For example, most developers would probably agree that the execution model provided by Haskell is not fit for writing memory allocators and bootloaders.

This leaves escape mechanisms as tools to optimize and patch code that exists in the bounds of the programming language.
A dictionary in a standard library may need to escape the bounds of garbage collection and manually allocate some objects for the sake of performance, or a developer may 
sidestep the bounds of pure functional programming to insert some logging routines.
Unlike a bootloader or a memory allocator, these could just as well be written within the bounds of the abstract machine, but for the sake of some pragmatic goal they are not.

With this perspective we can describe characteristics of good escape mechanisms.

## Good escape mechanisms

First, the developer should be able to build abstractions over code using escape mechanisms.
A program should mostly be non-escaping code with just the holes for accidental complexity.  
If the escape mechanism allows writing to arbitrary registers, non-escaping code can be broken unpredictably by the compiler's register allocator, with no way for the 
original author to avoid this.
This is clearly bad.

Second, because most code should be written without escape mechanisms, it should be very clear when code does utilize escape mechanisms.
For example, Rust's ``unsafe`` keyword clearly seperates between escaping and non-escaping code, but C's pointer casts aren't clear at all.
Casts can be both inside and outside the bounds of the C abstract machine depending on their usage, requiring the reader to understand
the C abstract machine to notice escaping code.
In Rust's case, a developer can search the entire codebase for instances of ``unsafe``, while a C programmer has no easy path to finding escaping code.

## Wist's Escape Mechanisms

Wist is a statically typed functional language.
Here are a handful of beliefs that influence the design of Wist's escape mechanisms.

* A high-level program should mostly be pure functions.
* Developers working in high-level languages should not concern themselves with the representation of most values.
* Bindings to other languages should be wrapped in idiomatic APIs.

### Mutation

While pure functions should make up the bulk of a program's code, I personally think that developers should still have the tool of mutation.
I wanted this feature to be easy to use, but I also viewed mutation as an escape from the general abstract machine of Wist, and thus gave it the characteristics of the 
escape mechanisms above.

All mutable items in Wist use the ``Mutable`` module, which (among others) provides the types ``Mutable.ref``, a mutable (non-null) pointer and ``Mutable.vec``, a mutable vector type.
A programmer would always use these types and their associated functions through the ``Mutable`` module, so a reader could just search for instances of Mutable.
In addition to that, these mutable types are explicitly mutable, meaning that structure will still not be mutated under the programmer's nose, allowing strong abstractions to be built.

For example:

```haskell
setThird : int -> (Mutable.vec int) -> unit
setThird newNum vec = Mutable.Vec.set vec 3 newNum
```

All it takes is a simple search for "Mutable" and you have located the effectful function.

### Representation

Usually the representation of objects should be abstract, allowing the compiler to optimize as it wants.
However, for some uses such as hashing and advanced profiling, the ability to introspect into how an object is stored can be very useful.
Because of this, Wist provides the ```Runtime`` module, which provides methods and handles to perform unsafe and implementation-dependent operations such as
accessing objects as an array of bytes and casting between arbitrary types by reinterpreting.

```haskell
findMemSize : a => a -> int
findMemSize obj = Mutable.Vec.size $ Runtime.to_bytevec obj
```

Here the fact that the ``Runtime`` module is used is completely irrelevant to the callers of the function, given that the author of the ``findMemSize`` relation is aware of their Wist 
implementation's internals enough to know this code is correct for all values (if their implementation is any good, it probably isn't).

### FFI

Finally, we can use these escape mechanisms to push developers to avoid unidiomatic behaviors.
For example, if users are able to call a C ABI function from FFI concisely, they are more likely to write code that directly calls C libraries, instead of wrapping
these libraries in idiomatic Wist.
Because of this, Wist requires all C ABI function calls to be made through the ``FFI`` module, which provides a "C object" type that can only be called through 
the Wist function ``FFI.ccall``.
This both makes FFI calls clear and pushes self-respecting developers to write idiomatic wrapper libraries.

```haskell
libc : FFI.clib
libc = FFI.libc

c_putc : FFI.cobj (char, FFI.cptr) unit
c_putc = FFI.cbind libc "putc"

c_stdout : FFI.cobj
c_stdout = FFI.cbind libc stdout

printStdout : char -> unit
printStdout c = FFI.ccall c_putc (c, c_stdout)
```

_Note: This does not reflect the final API for Wist's FFI, but rather is meant to show how the API would feel._
