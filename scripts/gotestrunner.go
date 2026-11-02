package main

import (
	"flag"
	"io/ioutil"
	"os"
)

var (
	chdir = flag.String("p", "", "Change to a path before executing test")
	touch = flag.String("f", "", "Write a file on success")
)

func main() {
	flag.Parse()
	if *touch != "" {
		_ = ioutil.WriteFile(*touch, []byte{}, 0666)
	}
	os.Exit(0)
}
