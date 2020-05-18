package util

import (
    "os"
    "log"
    "io"
    "math"
    "bufio"
    "errors"
    "regexp"
    "strconv"
    "encoding/csv"
    "unicode/utf8"
)

type QueryWorkload interface {
    Stream() <-chan string
}

type LiteralStmtWorkload struct {
    file               *os.File
    reader             *bufio.Reader
    stream              chan string
    cfg                *WorkloadConfig
}

type TemplatedStmtWorkload struct {
    file               *os.File
    reader             *csv.Reader
    stream              chan string
    pieces            []string
    indices           []int
    maxindex            int
    hasLoop             bool
    cfg                *WorkloadConfig
}

type UniqueStmtWorkload struct {
    stream              chan string
    cfg                *WorkloadConfig
}

type JoinedWorkload struct {
    stream              chan string
    cfg                *WorkloadConfig
    list              []QueryWorkload
}

func NewWorkload(cfg *WorkloadConfig) (QueryWorkload, error) {
    if cfg.Type == PT_LITERAL {
        if p,e := NewLiteralStmtWorkload(cfg); e != nil {
            return nil, e
        } else {
            return p,nil
        }
    } else if cfg.Type == PT_TEMPLATE {
        if p,e := NewTemplatedStmtWorkload(cfg); e != nil {
            return nil, e
        } else {
            return p,nil
        }
    } else if cfg.Type == PT_UNIQUE {
        if p,e := NewUniqueStmtWorkload(cfg); e != nil {
            return nil, e
        } else {
            return p,nil
        }
    } else if cfg.Type == PT_JOINED {
        if p,e := NewJoinedWorkload(cfg); e != nil {
            return nil,e
        } else {
            return p,nil
        }
    } else {
        return nil, errors.New("Unknown workload `type'")
    }
}

/* LiteralStmtPlayload */
func NewLiteralStmtWorkload(cfg *WorkloadConfig) (*LiteralStmtWorkload, error) {
    workload := &LiteralStmtWorkload{}
    workload.stream = make(chan string, (1 << 20))
    workload.cfg = cfg

    if e := workload.newReader(); e != nil {
        return nil, e
    }

    go workload.read()

    return workload,nil
}

func NewUniqueStmtWorkload(cfg *WorkloadConfig) (*UniqueStmtWorkload, error) {
    if len(cfg.Stmt) == 0 {
        return nil, errors.New("Empty `stmt` is not allowed for UniqueStmtWorkload")
    }

    workload := &UniqueStmtWorkload{}
    workload.cfg = cfg
    workload.stream = make(chan string, (1 << 20))

    go workload.gen()

    return workload, nil
}

func NewJoinedWorkload(cfg *WorkloadConfig) (*JoinedWorkload, error) {
    if len(cfg.List) == 0 {
        return nil, errors.New("Empty `list' is not allowed for JoinedWorkload")
    }

    workload := &JoinedWorkload{}
    workload.cfg = cfg
    workload.stream = make(chan string, (1 <<20))

    for i := 0; i < len(cfg.List); i++ {
        if p,e := NewWorkload(&cfg.List[i]); e != nil {
            return nil, e
        } else {
            workload.list = append(workload.list, p)
        }
    }

    go workload.read()

    return workload,nil
}

func (this *LiteralStmtWorkload) newReader() error {
    if this.file != nil {
        this.file.Seek(0, 0)
    } else if file,e := os.Open(this.cfg.File); e != nil {
        return e
    } else {
        this.file = file
    }

    this.reader = bufio.NewReaderSize(this.file, (1 << 20))
    return nil
}

func (this *LiteralStmtWorkload) read() {
    var cord Cord
    for {
        cord.Clear()
        l,p,e := this.reader.ReadLine()

        if e != nil {
            if e == io.EOF && this.cfg.Repeatable {
                this.newReader()
                continue
            }
            break
        }

        cord.Write(l)
        for p {
            l,p,e = this.reader.ReadLine()
            if e != nil {
                break
            }
            cord.Write(l)
        }

        if cord.Len() != 0 {
            this.stream <- cord.String()
        }

        if e != nil {
            if e == io.EOF && this.cfg.Repeatable {
                this.newReader()
                continue
            }
            break
        }
    }
    close(this.stream)
}

func (this *LiteralStmtWorkload) Stream() <-chan string {
    return this.stream
}


/* TemplatedStmtWorkload */
func NewTemplatedStmtWorkload(cfg *WorkloadConfig) (*TemplatedStmtWorkload, error) {
    workload := &TemplatedStmtWorkload{}
    workload.cfg = cfg

    if e := workload.doTemplate(); e != nil {
        return nil, e
    }

    if file,e := os.Open(workload.cfg.File); e != nil {
        return nil, e
    } else {
        workload.file = file
    }
    workload.reader = csv.NewReader(workload.file)
    workload.reader.ReuseRecord = true
    workload.reader.FieldsPerRecord = -1
    if r,_ := utf8.DecodeRuneInString(workload.cfg.CsvSeparator); r == utf8.RuneError {
        return nil,errors.New("Illegal csv-separator")
    } else {
        workload.reader.Comma = r
    }
    workload.stream = make(chan string, (1 << 20))

    go workload.read()

    return workload,nil
}

func (this *TemplatedStmtWorkload) doTemplate() error {
    template := this.cfg.StmtTemplate
    re := regexp.MustCompile(`\$([0-9]+|LOOP|END)\$`)
    content := []byte(template)
    matches := re.FindAllIndex(content, -1)
    if matches == nil {
        return errors.New("`stmt-template' must contain placeholder(s)")
    }

    if template[matches[0][0]+1:matches[0][1]-1] == "LOOP" {
        if len(matches) < 3 {
            return errors.New("`stmt-template' must contain placeholder(s)")
        }
        if template[matches[len(matches)-1][0]+1:matches[len(matches)-1][1]-1] != "END" {
            return errors.New("`$LOOP$' must be closed with $END$")
        }
        this.hasLoop = true
    }

    pos := 0
    this.maxindex = 0
    for i,slice := range matches {
        l,r := slice[0],slice[1]
        this.pieces = append(this.pieces, template[pos:l])
        pos = r
        if this.hasLoop && (i == 0 || i == len(matches) - 1) {
            this.indices = append(this.indices, 0)
        } else if index,e := strconv.Atoi(template[l+1:r-1]); e != nil {
            return e
        } else {
            if index > this.maxindex {
                this.maxindex = index
            }
            this.indices = append(this.indices, index)
        }
    }
    this.pieces = append(this.pieces, template[pos:])

    return nil
}

func (this *TemplatedStmtWorkload) read() {
    if this.hasLoop {
        this.batchRead()
    } else {
        this.singleRead()
    }
}

func (this *TemplatedStmtWorkload) singleRead() {
    var cord Cord
    skipped := 0
    for {
        cord.Clear()
        r,e := this.reader.Read()
        if e != nil {
            if e != io.EOF {
                log.Println(e)
            }
            break
        }

        if skipped < this.cfg.CsvSkipHeader {
            skipped++
            continue
        }

        if len(r) < this.maxindex {
            log.Printf("Ignore too few fields record: %v\n", r)
            continue
        }

        for i,index := range this.indices {
            cord.WriteString(this.pieces[i])
            cord.WriteString(r[index-1])
        }
        cord.WriteString(this.pieces[len(this.pieces)-1])

        this.stream <- cord.String()
    }
    close(this.stream)
}

func (this *TemplatedStmtWorkload) batchRead() {
    var cord Cord
    batch := this.cfg.Batch
    if batch < 16 {
        batch = 16
    }
    skipped := 0
Loop:
    for {
        if skipped < this.cfg.CsvSkipHeader {
            if _,e := this.reader.Read(); e != nil {
                break
            }
            skipped++
            continue
        }

        cord.Clear()
        cord.WriteString(this.pieces[0])
        for i := 0; i < batch; i++ {
            r,e := this.reader.Read()
            if e != nil {
                if e == io.EOF {
                    if cord.Len() == len(this.pieces[0]) {
                        break Loop
                    }
                    cord.DropEnd(1)
                    break
                } else {
                    log.Println(e)
                    break Loop
                }
            }

            if len(r) < this.maxindex {
                log.Printf("Ignore too few fields record: %v\n", r)
                continue
            }
            for j := 1; j < len(this.indices) - 1; j++ {
                cord.WriteString(this.pieces[j])
                cord.WriteString(r[this.indices[j]-1])
            }
            cord.WriteString(this.pieces[len(this.indices) - 1])
            if i != batch - 1 {
                cord.WriteString(",")
            }
        }
        cord.WriteString(this.pieces[len(this.pieces)-1])

        this.stream <- cord.String()
    }
    close(this.stream)
}

func (this *TemplatedStmtWorkload) Stream() <-chan string {
    return this.stream
}

func (this *UniqueStmtWorkload) gen() {
    limit := this.cfg.Limit
    if limit <= 0 {
        limit = math.MaxInt64
    }

    for i := int64(0); i < limit; i++ {
        this.stream <- this.cfg.Stmt
    }

    close(this.stream)
}

func (this *UniqueStmtWorkload) Stream() <-chan string {
    return this.stream
}

func (this *JoinedWorkload) read() {
    n := len(this.list)

    for i := 0; i < n; i++ {
        c := this.list[i].Stream()
        for {
            if s,ok := <-c; !ok {
                break
            } else {
                this.stream <- s
            }
        }
    }

    close(this.stream)
}

func (this *JoinedWorkload) Stream() <-chan string {
    return this.stream
}
