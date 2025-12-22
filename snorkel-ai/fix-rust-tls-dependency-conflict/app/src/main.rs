use std::error::Error;

#[tokio::main]
async fn main() -> Result<(), Box<dyn Error>> {
    // This code uses reqwest which will pull in native-tls/openssl-sys
    // and tokio-rustls which uses rustls, creating a conflict
    let client = reqwest::Client::new();
    let response = client.get("https://httpbin.org/get").send().await?;
    let text = response.text().await?;
    println!("Response: {}", text);
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_client_creation() {
        let client = reqwest::Client::new();
        assert!(client.get("https://httpbin.org/get").build().is_ok());
    }

    #[test]
    fn test_basic() {
        assert_eq!(1 + 1, 2);
    }
}

