import { getSafeAccountByAddr } from '../SafeApiKit.ts'
const addr = "0xf5103fC80db8b82e3d922bd6dB81dE1Fe024f540"


const result = await getSafeAccountByAddr("11155111", addr)
console.log(result)