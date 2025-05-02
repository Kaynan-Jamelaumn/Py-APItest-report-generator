from PyTestDocx import BaseAPITest
import unittest

class TestBillingOperations(BaseAPITest):
    """Tests for billing-related endpoints"""
    
    def setUp(self):
        """Prepare authenticated session for billing tests"""
        response = self.login()
        if response.status_code != 200:
            self.skipTest("Authentication failed for billing tests")

    def test_update_transaction(self):
        """Should successfully update a billing transaction"""
        payload = {
            "id": 1,
            "id_plano": 1,
            "valor_plano": 2999,
            "id_tipo_pagamento": 1,
            "id_recorrencia": 1,
            "melhor_dia": 5,
            "cartao_bandeira": "Master",
            "cartao_final": "1234",
            "cartao_vencimento": "10/24"
        }
        
        response = self.session.put(
            f"{self.base_url}/transaction-data",
            json=payload,
            headers=self.auth_headers()
        )
        
        self.assert_response(response, 200)
        self.assertEqual(response.json()['id'], 1)

    def test_retrieve_transaction(self):
        """Should fetch existing transaction data"""
        response = self.session.get(
            f"{self.base_url}/get-transaction-data/2",
            headers=self.auth_headers()
        )
        
        self.assert_response(response, 200)
        self.assertIn('id_plano', response.json())




    # def test_create_client(self):
    #     """Should successfully create a new client"""
    #     payload = {
    #         "providerId": 1,
    #         "accountType": 1,
    #         "agencyCode": "258",
    #         "agencyName": "Santander",
    #         "holderName": "Caua P",
    #         "holderCpfCnpj": "13248666919",
    #         "pixKeyType": "cpf",
    #         "pixKey": "13248666919"
    #     }
        
    #     response = self.session.post(
    #         f"{self.base_url}/oac/payment",
    #         json=payload,
    #         headers=self.auth_headers()
    #     )
        
    #     self.assert_response(response, 201)
    #     self.assertIn('id', response.json())

########################################################################

    # def test_list_financial_institutions(self):
    #     """Should fetch a list of financial institutions"""
    #     response = self.session.get(
    #         f"{self.base_url}/oac/customer/all",
    #         headers=self.auth_headers()
    #     )
        
    #     self.assert_response(response, 200)
    #     self.assertIn('customers', response.json())
    #     self.assertIsInstance(response.json()['customers'], list)

    # def test_list_agencies(self):
    #     """Should fetch a list of agencies"""
    #     response = self.session.get(
    #         f"{self.base_url}/oac/customer/all",
    #         headers=self.auth_headers()
    #     )
        
    #     self.assert_response(response, 200)
    #     self.assertIn('customers', response.json())
    #     self.assertIsInstance(response.json()['customers'], list)


    # def test_create_client_contract(self):
    #     """Should successfully create a client contract"""
    #     payload = {
    #         "tipo": "atualizar",
    #         "id": "-1",
    #         "instituicao": "45",
    #         "tipocontrato": "2",
    #         "periodicidade": "1",
    #         "sla": "3",
    #         "prazo": "12",
    #         "inicio": "2023-01-01",
    #         "fim": "2023-12-31",
    #         "pecas": "1",
    #         "servicos": "1",
    #         "alcada": "1000.00",
    #         "deslocamento": "200",
    #         "valorPreventivas": "500.00",
    #         "valorKmCorretiva": "0.50",
    #         "frete": "100",
    #         "monitoramento": "1",
    #         "custos_extras": "50",
    #         "num_contrato": "ABC123",
    #         "ultima_renovacao": "2023-06-01",
    #         "prox_vencimento": "2024-06-01",
    #         "reajuste_contratual": "5.0",
    #         "indice_correcao": "1.5",
    #         "impostos": "10",
    #         "lpu": "1",
    #         "rat": "0",
    #         "quantidade": "100",
    #         "condicao_pagamento": "2",
    #         "valor": "10000.00",
    #         "fechamento": "2023-06-01",
    #         "operacao_remota": "1",
    #         "alertas": "1",
    #         "valor_alerta": "500.00"
    #     }
        
    #     response = self.session.post(
    #         f"{self.base_url}/app/classes/contratos-classe.php",
    #         data=payload,
    #         headers=self.auth_headers()
    #     )
        
    #     self.assert_response(response, 201)
    #     self.assertIn('id', response.json())



    # def test_create_charge_boleto_month(self):
    #     """Should create a charge with boleto payment method and monthly interval"""
    #     payload = {
    #         "id_client": "852",
    #         "payment_method": "boleto",
    #         "interval": "month",
    #         "billing_days": "",
    #         "billing_day": 10,
    #         "price": 10,
    #         "customer": {
    #             "name": "Tony Stark",
    #             "email": "tcr.thiago@gmail.com",
    #             "document": "05886892974",
    #             "phones": {
    #                 "mobile_phone": {
    #                     "country_code": "55",
    #                     "area_code": "48",
    #                     "number": "991938533"
    #                 }
    #             }
    #         }
    #     }
        
    #     response = self.session.post(
    #         f"{self.base_url}/charge",
    #         json=payload,
    #         headers=self.auth_headers()
    #     )
        
    #     self.assert_response(response, 201)
    #     self.assertIn('id', response.json())



    # def test_create_charge_boleto_year(self):
    #     """Should create a charge with boleto payment method and yearly interval"""
    #     payload = {
    #         "id_client": "1234",
    #         "payment_method": "boleto",
    #         "interval": "year",
    #         "billing_days": 10,
    #         "billing_day": "",
    #         "price": 10,
    #         "customer": {
    #             "name": "Tony Stark",
    #             "email": "tcr.thiago@gmail.com",
    #             "document": "603.810.030-00",
    #             "phones": {
    #                 "mobile_phone": {
    #                     "country_code": "55",
    #                     "area_code": "48",
    #                     "number": "991938533"
    #                 }
    #             }
    #         }
    #     }
        
    #     response = self.session.post(
    #         f"{self.base_url}/api/charge",
    #         json=payload,
    #         headers=self.auth_headers()
    #     )
        
    #     self.assert_response(response, 201)
    #     self.assertIn('id', response.json())

    # def test_create_charge_credit_card_year(self):
    #     """Should create a charge with credit card payment method and yearly interval"""
    #     payload = {
    #         "id_client": "5232",
    #         "payment_method": "credit_card",
    #         "interval": "year",
    #         "billing_days": 10,
    #         "billing_day": "",
    #         "customer": {
    #             "name": "Tony Stark",
    #             "email": "avengerstark@ligadajustica.com.br",
    #             "document": "06126037928",
    #             "type": "individual",
    #             "phones": {
    #                 "mobile_phone": {
    #                     "country_code": "55",
    #                     "area_code": "48",
    #                     "number": "991938533"
    #                 }
    #             }
    #         },
    #         "price": 10,
    #         "card": {
    #             "number": "4000000000000010",
    #             "holder_name": "Tony Stark",
    #             "exp_month": "1",
    #             "exp_year": "30",
    #             "cvv": "3531",
    #             "billing_address": {
    #                 "line_1": "10880, Malibu Point, Malibu Central",
    #                 "zip_code": "88104410",
    #                 "city": "Malibu",
    #                 "state": "SC",
    #                 "country": "BR"
    #             }
    #         }
    #     }
        
    #     response = self.session.post(
    #         f"{self.base_url}/api/charge",
    #         json=payload,
    #         headers=self.auth_headers()
    #     )
        
    #     self.assert_response(response, 201)
    #     self.assertIn('id', response.json())

    # def test_create_charge_credit_card_month(self):
    #     """Should create a charge with credit card payment method and monthly interval"""
    #     payload = {
    #         "id_client": "1234",
    #         "payment_method": "credit_card",
    #         "interval": "month",
    #         "billing_days": "",
    #         "billing_day": 10,
    #         "customer": {
    #             "name": "Tony Stark",
    #             "email": "avengerstark@ligadajustica.com.br",
    #             "document": "06126037928",
    #             "type": "individual",
    #             "phones": {
    #                 "mobile_phone": {
    #                     "country_code": "55",
    #                     "area_code": "48",
    #                     "number": "991938533"
    #                 }
    #             }
    #         },
    #         "price": 10,
    #         "card": {
    #             "number": "4000000000000010",
    #             "holder_name": "Tony Stark",
    #             "exp_month": "1",
    #             "exp_year": "30",
    #             "cvv": "3531",
    #             "billing_address": {
    #                 "line_1": "10880, Malibu Point, Malibu Central",
    #                 "zip_code": "88104410",
    #                 "city": "Malibu",
    #                 "state": "SC",
    #                 "country": "BR"
    #             }
    #         }
    #     }
        
    #     response = self.session.post(
    #         f"{self.base_url}/api/charge",
    #         json=payload,
    #         headers=self.auth_headers()
    #     )
        
    #     self.assert_response(response, 201)
    #     self.assertIn('id', response.json())

    # def test_cancel_charge(self):
    #     """Should cancel a charge"""
    #     payload = {
    #         "id_client": "1"
    #     }
        
    #     response = self.session.delete(
    #         f"{self.base_url}/api/cancellation",
    #         json=payload,
    #         headers=self.auth_headers()
    #     )
        
    #     self.assert_response(response, 200)

    # def test_create_payment_credit_card(self):
    #     """Should create a payment with credit card"""
    #     payload = {
    #         "kind": "creditCard",
    #         "items": [
    #             {
    #                 "amount": 1,
    #                 "description": "1",
    #                 "quantity": 1
    #             }
    #         ],
    #         "customer": {
    #             "name": 1,
    #             "email": "avengerstark@ligadajustica.com.br",
    #             "document": "603.810.030-00",
    #             "phones": {
    #                 "mobile_phone": {
    #                     "country_code": "55",
    #                     "area_code": "48",
    #                     "number": "991938533"
    #                 }
    #             }
    #         },
    #         "payments": [
    #             {
    #                 "payment_method": "creditCard",
    #                 "credit_card": {
    #                     "recurrence": False,
    #                     "installments": "1",
    #                     "statement_descriptor": "AVENGERS",
    #                     "card": {
    #                         "number": "4000000000000010",
    #                         "holder_name": "Tony Stark",
    #                         "exp_month": 1,
    #                         "exp_year": 30,
    #                         "cvv": 431,
    #                         "billing_address": {
    #                             "line_1": "10880, Malibu Point, Malibu Central",
    #                             "zip_code": "88104410",
    #                             "city": "Bala",
    #                             "state": "SC"
    #                         }
    #                     }
    #                 }
    #             }
    #         ]
    #     }
        
    #     response = self.session.post(
    #         f"{self.base_url}/api/payment",
    #         json=payload,
    #         headers=self.auth_headers()
    #     )
        
    #     self.assert_response(response, 201)
    #     self.assertIn('id', response.json())

    # def test_create_payment_boleto(self):
    #     """Should create a payment with boleto"""
    #     payload = {
    #         "kind": "bankSlip",
    #         "items": [
    #             {
    #                 "amount": 1000,
    #                 "description": "Pagamento",
    #                 "quantity": 1
    #             }
    #         ],
    #         "customer": {
    #             "name": "João",
    #             "email": "teste.teste@gmail.com",
    #             "document": "603.810.030-00",
    #             "type": "Individual",
    #             "address": {
    #                 "line_1": "375, Av. General Justo, Centro",
    #                 "line_2": "8º andar",
    #                 "zip_code": "20021130",
    #                 "city": "Rio de Janeiro",
    #                 "state": "RJ"
    #             }
    #         },
    #         "payments": [
    #             {
    #                 "payment_method": "boleto",
    #                 "boleto": {
    #                     "instructions": "1"
    #                 }
    #             }
    #         ]
    #     }
        
    #     response = self.session.post(
    #         f"{self.base_url}/api/payment",
    #         json=payload,
    #         headers=self.auth_headers()
    #     )
        
    #     self.assert_response(response, 201)
    #     self.assertIn('id', response.json())