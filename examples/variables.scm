(define var)

(define fn (lambda ()
	(define inner (lambda ()
		(set! var "still in global scope")
		0))
	(inner)))

(fn)

(display var)  ; Expect "still in global scope"
(newline)
