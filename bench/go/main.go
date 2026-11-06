// SPDX-License-Identifier: Apache-2.0
package main
import (
 "fmt"
 "os"
 "path/filepath"
 "sort"
 "strconv"
 "strings"
 "time"
 "github.com/bmatcuk/doublestar/v4"
)
func main() {
 if os.Args[3] == "walk" { walk(); return }
 data, err := os.ReadFile(os.Args[1]); if err != nil { panic(err) }
 count, err := strconv.Atoi(os.Args[2]); if err != nil || count < 1 { panic("iterations") }
 var rows [][]string
 for _, line := range strings.Split(strings.TrimSpace(string(data)), "\n") { rows = append(rows, strings.Split(line, "\t")) }
 for start := 0; start < len(rows); {
  end := start+1
  for end < len(rows) && rows[end][0] == rows[start][0] { end++ }
  group := rows[start:end]
  for _, row := range group { hit, e := doublestar.Match(row[1],row[2]); if e != nil || hit != (row[3]=="1") { panic(row) } }
  expected := 0; for i:=0;i<count;i++ { if group[i%len(group)][3]=="1" { expected++ } }
  sum:=0; began:=time.Now()
  for i:=0;i<count;i++ { row:=group[i%len(group)]; hit,e:=doublestar.Match(row[1],row[2]); if e!=nil { panic(e) }; if hit { sum++ } }
  elapsed:=time.Since(began).Nanoseconds()
  if sum != expected { panic("checksum") }
  fmt.Printf("%s\t%d\t%d\t%d\n",group[0][0],elapsed,count,sum)
  start=end
 }
}

func walk() {
 root:=os.Args[1]; count,err:=strconv.Atoi(os.Args[2]); if err!=nil { panic(err) }
 collect:=func() []string { paths,e:=doublestar.Glob(os.DirFS(root), "**/*.goose", doublestar.WithFilesOnly(), doublestar.WithNoFollow(), doublestar.WithFailOnIOErrors()); if e!=nil { panic(e) }; return paths }
 checksum:=func(paths []string) int64 { sum:=int64(len(paths))*1000003; for _,p:=range paths { sum+=int64(len(p)) }; return sum }
 paths:=collect(); sort.Strings(paths)
 expectedText,err:=os.ReadFile(filepath.Join(filepath.Dir(root),"walk-expected.txt"));if err!=nil { panic(err) }
 if strings.Join(paths,"\n")+"\n"!=string(expectedText) { panic("path set") }
 expected:=checksum(paths); var sum int64; began:=time.Now()
 for i:=0;i<count;i++ { sum+=checksum(collect()) }
 ns:=time.Since(began).Nanoseconds(); if sum!=expected*int64(count) { panic("checksum") }
 fmt.Printf("walk\t%d\t%d\t%d\n",ns,count,sum)
}
