import type {Wallet} from "../accounts/Wallet.ts";
import {type Address, parseGwei, type PublicClient} from "viem";

export async function sendFundtoSafe(amount: bigint, wallet:Wallet, safeAddress:Address) {
    const walletClient = wallet.walletClient
    const txhash = await walletClient.sendTransaction({
        account: wallet.getControllerAccount(),
        to: safeAddress,
        value: parseGwei(amount.toString())
    })
    console.log(txhash)
    const publicClient = wallet.publicClient
    const txReceipt = await publicClient.waitForTransactionReceipt({hash: txhash})
    return txReceipt
}