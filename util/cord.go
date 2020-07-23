package util

type Cord struct {
	b []byte
}

func (this *Cord) Len() int {
	return len(this.b)
}

func (this *Cord) Empty() bool {
	return len(this.b) == 0
}

func (this *Cord) Cap() int {
	return cap(this.b)
}

func (this *Cord) Clear() {
	this.b = this.b[0:0]
}

func (this *Cord) Write(s []byte) {
	prev, delta := len(this.b), len(s)
	this.Grow(delta)
	this.b = this.b[:prev+delta]
	copy(this.b[prev:], s)
}

func (this *Cord) WriteString(s string) {
	this.Grow(len(s))
	prev, delta := len(this.b), len(s)
	this.Grow(delta)
	this.b = this.b[:prev+delta]
	copy(this.b[prev:], s)
}

func (this *Cord) Grow(delta int) {
	left := cap(this.b) - len(this.b)
	if left >= delta {
		return
	}

	grown := len(this.b) + delta*4
	bb := make([]byte, grown)
	bb = bb[:len(this.b)]
	copy(bb, this.b)
	this.b = bb
}

func (this *Cord) DropEnd(n int) {
	this.b = this.b[0 : len(this.b)-n]
}

func (this *Cord) String() string {
	return string(this.b)
}
