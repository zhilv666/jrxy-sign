package main

import (
	"bytes"
	"crypto/aes"
	"crypto/cipher"
	"encoding/base64"
	"encoding/hex"
	"flag"
	"fmt"
	"os"
	"time"

	"github.com/gin-gonic/gin"
)

const (
	trueKey  = "hru89rwr87Nthifa"
	falseKey = "fafUY9659kyengTR"
)

var (
	host    = flag.String("host", "0.0.0.0", "Set the host address")
	port    = flag.Int("port", 10001, "Set the port number")
	path    = flag.String("path", "/jrxy", "Set the route address")
	version = flag.Bool("version", false, "Get the version number")
	help    = flag.Bool("help", false, "Get help")
	file    *os.File
)

func main() {
	flag.BoolVar(help, "h", false, "Get help")
	flag.BoolVar(version, "v", false, "Get the version number")
	flag.Parse()

	if *version {
		fmt.Println("Current version: 1.0.0")
		os.Exit(0)
	}

	if *help {
		flag.PrintDefaults()
		os.Exit(0)
	}

	file, _ = os.Create("jrxy_log_" + getCurrentTime() + ".log")

	router := gin.Default()
	router.POST(*path, jrxy)

	fmt.Println("Server is running...")
	fmt.Println("Please visit", fmt.Sprintf("%s:%d", *host, *port))

	router.Run(fmt.Sprintf("%s:%d", *host, *port))
}

func jrxy(ctx *gin.Context) {
	data, isOk := ctx.GetPostForm("data")
	if !isOk {
		ctx.JSON(200, gin.H{"code": -1, "data": "", "msg": "Data not found"})
		return
	}

	_type, _ := ctx.GetPostForm("type")
	isnews, _ := ctx.GetPostForm("isnews")

	var result string

	switch _type {
	case "encrypt":
		result = encryptoAes([]byte(data), isnews)
	case "decrypt":
		result = aesDecrypt(data, isnews)
	default:
		result = ""
	}

	console(_type, result)
	ctx.JSON(200, gin.H{"code": 200, "data": result, "msg": "Success"})
}

func base64Encode(data []byte) string {
	charset := "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
	var result []byte
	i := 0

	for i < len(data)-2 {
		i2 := (int(data[i]&255) << 16) | (int(data[i+1]&255) << 8) | int(data[i+2]&255)
		result = append(result, charset[(i2>>18)&63])
		result = append(result, charset[(i2>>12)&63])
		result = append(result, charset[(i2>>6)&63])
		result = append(result, charset[i2&63])
		i += 3

		if i%14 == 0 {
			result = append(result, ' ')
		}
	}

	if i < len(data) {
		i3 := int(data[i]&255) << 16

		if i+1 < len(data) {
			i3 |= int(data[i+1]&255) << 8
		}

		result = append(result, charset[(i3>>18)&63])
		result = append(result, charset[(i3>>12)&63])

		if i+1 < len(data) {
			result = append(result, charset[(i3>>6)&63])
		} else {
			result = append(result, '=')
		}

		result = append(result, '=')

		if i+1 >= len(data) {
			result = append(result, charset[i3&63])
		}
	}

	return string(result[:len(result)-1])
}

func pkcs5Padding(src []byte, blockSize int) []byte {
	padding := blockSize - len(src)%blockSize
	padtext := bytes.Repeat([]byte{byte(padding)}, padding)
	return append(src, padtext...)
}

func encryptoAes(textBytes []byte, isnews string) string {
	var keyBytes []byte

	switch isnews {
	case "true":
		keyBytes = []byte(trueKey)
	case "false":
		keyBytes = []byte(falseKey)
	}

	fmt.Println(string(keyBytes), isnews)
	ivBytes := []byte{1, 2, 3, 4, 5, 6, 7, 8, 9, 1, 2, 3, 4, 5, 6, 7}
	block, err := aes.NewCipher(keyBytes)

	if err != nil {
		return ""
	}

	plainTextBytes := pkcs5Padding(textBytes, block.BlockSize())
	mode := cipher.NewCBCEncrypter(block, ivBytes)
	encryptoBytes := make([]byte, len(plainTextBytes))
	mode.CryptBlocks(encryptoBytes, plainTextBytes)

	return base64Encode(encryptoBytes)
}

func unpadPKCS7(data []byte) ([]byte, error) {
	length := len(data)
	unpadding := int(data[length-1])

	if unpadding > length {
		return nil, fmt.Errorf("Invalid padding")
	}

	return data[:(length - unpadding)], nil
}

func aesDecrypt(ciphertext string, isnews string) string {
	key := "6661665559393635396b79656e675452"
	iv := "01020304050607080901020304050607"
	keyBytes, err := hex.DecodeString(key)

	if err != nil {
		return ""
	}

	ivBytes, err := hex.DecodeString(iv)

	if err != nil {
		return ""
	}

	cipherText, err := base64.StdEncoding.DecodeString(ciphertext)

	if err != nil {
		return ""
	}

	block, err := aes.NewCipher(keyBytes)

	if err != nil {
		return ""
	}

	mode := cipher.NewCBCDecrypter(block, ivBytes)
	mode.CryptBlocks(cipherText, cipherText)
	cipherText, err = unpadPKCS7(cipherText)

	if err != nil {
		return ""
	}

	return string(cipherText)
}

func getCurrentTime() string {
	currentTime := time.Now()
	year, month, day := currentTime.Date()
	hour, minute, second := currentTime.Clock()
	return fmt.Sprintf("%04d-%02d-%02d_%02d-%02d-%02d", year, month, day, hour, minute, second)
}

func console(key string, value string) {
	content := getCurrentTime() + " | " + key + "==>" + value
	file.Write([]byte(content + "\n"))
	fmt.Println(content)
}
